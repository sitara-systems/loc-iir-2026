#!/usr/bin/env python3
"""
LC Archive Search — Hidden in Plain Sight + What Did They Know?
Runs targeted keyword searches against the Library of Congress API and
Chronicling America, organized by research target from LC-Research-Targets.md.

Usage:
    pip install requests
    python lc_search.py

Output:
    LC-Search-Results.md  (in same directory as this script)

Notes:
    - No API key required; LC API is public
    - Rate-limited to ~1 req/sec to be respectful
    - Results are cursory keyword searches only — not vector/semantic search
    - Goal: confirm LC *does* hold relevant material; not exhaustive
"""

import requests
import json
import time
import os
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "LC-Search-Results.md")
DELAY = 1.2          # seconds between requests
RESULTS_PER_QUERY = 5  # how many items to show per query (increase to 10-25 for deeper review)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "research-preview/1.0 (IIR concept paper research; contact: nathan@sitara.systems)"})

# ── API HELPERS ─────────────────────────────────────────────────────────────

def search_loc(query, collection="search", count=RESULTS_PER_QUERY, extra_params=None):
    """
    Search loc.gov API.
    collection: 'search' (all), 'photos', 'maps', 'newspapers', 'manuscripts', 'legislation'
    """
    url = f"https://www.loc.gov/{collection}/"
    params = {"q": query, "fo": "json", "c": count}
    if extra_params:
        params.update(extra_params)
    try:
        r = SESSION.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def search_chronicling_america(query, language=None, date1=None, date2=None,
                                state=None, count=RESULTS_PER_QUERY):
    """
    Search Chronicling America full-text newspaper archive.
    language: 'spa' for Spanish, 'eng' for English, etc.
    """
    url = "https://chroniclingamerica.loc.gov/search/pages/results/"
    params = {"q": query, "format": "json", "rows": count}
    if language:
        params["language"] = language
    if date1:
        params["date1"] = date1
        params["dateFilterType"] = "yearRange"
    if date2:
        params["date2"] = date2
    if state:
        params["state"] = state
    try:
        r = SESSION.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def extract_loc_results(data):
    """Pull title, date, url, description from a loc.gov JSON response."""
    if "error" in data:
        return 0, [{"error": data["error"]}]
    total = data.get("pagination", {}).get("total", 0)
    items = []
    for r in data.get("results", []):
        items.append({
            "title": r.get("title", "").strip(),
            "date": r.get("date", ""),
            "url": r.get("url", r.get("id", "")),
            "description": " | ".join(r.get("description", []))[:200] if isinstance(r.get("description"), list) else str(r.get("description", ""))[:200],
            "subject": r.get("subject", []),
            "location": r.get("location", []),
        })
    return total, items


def extract_ca_results(data):
    """Pull title, date, newspaper, url from a Chronicling America JSON response."""
    if "error" in data:
        return 0, [{"error": data["error"]}]
    total = data.get("totalItems", 0)
    items = []
    for r in data.get("items", []):
        items.append({
            "title": r.get("title", ""),
            "date": r.get("date", ""),
            "newspaper": r.get("title_normal", ""),
            "state": r.get("edition_label", ""),
            "url": "https://chroniclingamerica.loc.gov" + r.get("id", ""),
            "ocr_snippet": r.get("ocr_eng", r.get("ocr_spa", ""))[:300] if r.get("ocr_eng") or r.get("ocr_spa") else "",
        })
    return total, items


# ── SEARCH PLAN ─────────────────────────────────────────────────────────────
# Each entry: (label, search_fn, args, kwargs, notes)

SEARCHES = [

    # ════════════════════════════════════════════════════════════════════════
    # PROJECT 1: HIDDEN IN PLAIN SIGHT
    # ════════════════════════════════════════════════════════════════════════

    # ── THREAD B: Nino-Dominguez ────────────────────────────────────────────

    ("1B-01 | FSA/OWI: Mexican railroad workers, Idaho",
     "loc", "photos",
     {"query": "mexican railroad workers idaho"},
     "Looking for visual documentation of Mexican labor in Idaho railroad corridor"),

    ("1B-02 | FSA/OWI: Railroad section gang Southwest",
     "loc", "photos",
     {"query": "railroad section gang southwest laborers"},
     "Section gangs = the labor category the Nino family likely falls under"),

    ("1B-03 | FSA/OWI: Railroad outfit car / labor camp",
     "loc", "photos",
     {"query": "railroad outfit car labor camp workers"},
     "Outfit cars = the mobile homes the family lived in 1927-1930"),

    ("1B-04 | FSA/OWI: Azusa / San Gabriel Valley California",
     "loc", "photos",
     {"query": "Azusa California labor workers"},
     "Family settled at 140 Pasadena Ave, Azusa by 1930"),

    ("1B-05 | FSA/OWI: San Gabriel Canyon / dam construction",
     "loc", "photos",
     {"query": "San Gabriel Canyon dam construction laborers California"},
     "Felipe Nino likely worked Morris Dam, San Gabriel Canyon, ~1930-1935"),

    ("1B-06 | Chronicling America (Spanish): Repatriación 1929-1936",
     "ca", None,
     {"query": "repatriacion mexicanos", "language": "spa", "date1": "1929", "date2": "1936"},
     "Spanish-language coverage of Mexican Repatriation — La Prensa, La Opinión"),

    ("1B-07 | Chronicling America (Spanish): Deportación California 1929-1936",
     "ca", None,
     {"query": "deportacion California", "language": "spa",
      "date1": "1929", "date2": "1936", "state": "California"},
     "California Spanish-language press coverage of deportation/repatriation"),

    ("1B-08 | Chronicling America (Spanish): Ferrocarril (railroad) workers",
     "ca", None,
     {"query": "ferrocarril trabajadores mexicanos", "language": "spa",
      "date1": "1920", "date2": "1935"},
     "Spanish coverage of Mexican railroad workers"),

    ("1B-09 | Maps: El Paso to Idaho railroad corridor",
     "loc", "maps",
     {"query": "railroad map El Paso Idaho Pacific"},
     "Rail corridor the family traveled — El Paso to Idaho 1927"),

    ("1B-10 | Maps: Southern Pacific Railroad Southwest",
     "loc", "maps",
     {"query": "Southern Pacific Railroad map Southwest 1920"},
     "Southern Pacific operated main lines through this corridor"),

    ("1B-11 | LOC General: Mexican Repatriation congressional record",
     "loc", "search",
     {"query": "Mexican Repatriation deportation Congress 1930"},
     "Congressional debate and documentation of the Repatriation"),

    ("1B-12 | LOC General: Immigration Act 1924 Mexican exemption",
     "loc", "search",
     {"query": "Immigration Act 1924 Mexican exemption Western Hemisphere"},
     "The specific provision that exempted Western Hemisphere from quotas — why the Nino family could cross at all"),

    # ── THREAD A: Khan / Mohaiyuddin ────────────────────────────────────────

    ("1A-01 | LOC General: Bhagat Singh Thind case",
     "loc", "search",
     {"query": "Bhagat Singh Thind naturalization Supreme Court"},
     "The 1923 Supreme Court case that closed the racial eligibility door"),

    ("1A-02 | Chronicling America: Thind case coverage, New York papers 1923",
     "ca", None,
     {"query": "Thind naturalization Hindu white", "date1": "1922", "date2": "1924"},
     "Newspaper coverage of the Thind decision — how widely reported was it?"),

    ("1A-03 | LOC General: South Asian naturalization British subject white",
     "loc", "search",
     {"query": "Hindu naturalization British subject white citizenship 1910 1920"},
     "The legal argument Mohaiyuddin used — British colonial status as whiteness"),

    ("1A-04 | LOC General: Commissioner General Annual Reports immigration",
     "loc", "search",
     {"query": "Commissioner General Immigration Annual Report 1913 1919 South Asian"},
     "Annual reports document naturalization patterns by origin — may track British Guiana / Hindu petitions"),

    ("1A-05 | LOC General: Dillingham Commission immigration report",
     "loc", "search",
     {"query": "Dillingham Commission immigration report East Indian"},
     "1910-1911 commission report that set the stage for the 1924 Act"),

    ("1A-06 | Chronicling America: British Guiana immigrants New York 1910-1920",
     "ca", None,
     {"query": "British Guiana New York immigrant", "date1": "1910", "date2": "1925"},
     "Coverage of the Indo-Caribbean immigrant community Mohaiyuddin was part of"),

    ("1A-07 | LOC General: 1924 Immigration Act committee hearings",
     "loc", "search",
     {"query": "Immigration Act 1924 House Committee hearings Johnson-Reed"},
     "Congressional hearings where the racial eligibility provisions were debated"),

    # ════════════════════════════════════════════════════════════════════════
    # PROJECT 2: WHAT DID THEY KNOW?
    # ════════════════════════════════════════════════════════════════════════

    ("2-01 | LOC General: PSAC 1965 atmospheric carbon dioxide report",
     "loc", "search",
     {"query": "President Science Advisory Committee carbon dioxide atmosphere 1965"},
     "The 1965 PSAC report is the first federal acknowledgment of climate risk"),

    ("2-02 | LOC General: Lyndon Johnson climate conservation message 1965",
     "loc", "search",
     {"query": "Lyndon Johnson conservation natural beauty message Congress 1965"},
     "LBJ's February 1965 message to Congress mentioning atmospheric CO2"),

    ("2-03 | LOC General: Roger Revelle carbon dioxide testimony Congress",
     "loc", "search",
     {"query": "Roger Revelle carbon dioxide Congress testimony climate"},
     "Revelle testified to Congress multiple times on CO2 — key witness"),

    ("2-04 | LOC Photos: USGS glacier photographs historical",
     "loc", "photos",
     {"query": "glacier retreat mountain ice historical survey"},
     "USGS historical glacier photographs documenting retreat"),

    ("2-05 | LOC General: Weather Bureau temperature records climate",
     "loc", "search",
     {"query": "Weather Bureau temperature climate records 1950 1960"},
     "Historical Weather Bureau climate data and reports"),

    ("2-06 | Chronicling America: Carbon dioxide climate atmosphere 1960s",
     "ca", None,
     {"query": "carbon dioxide atmosphere climate warming", "date1": "1960", "date2": "1975"},
     "Public press coverage of early climate science — how widely known was it?"),

]

# ── OUTPUT ──────────────────────────────────────────────────────────────────

def run_search(entry):
    label, api_type, collection, kwargs, notes = entry
    time.sleep(DELAY)

    if api_type == "loc":
        data = search_loc(kwargs["query"], collection=collection,
                          extra_params={k: v for k, v in kwargs.items() if k != "query"})
        total, items = extract_loc_results(data)
    else:  # "ca"
        ca_kwargs = {k: v for k, v in kwargs.items()}
        query = ca_kwargs.pop("query")
        data = search_chronicling_america(query, **ca_kwargs)
        total, items = extract_ca_results(data)

    return total, items


def format_item(item, api_type):
    if "error" in item:
        return f"  ⚠️  Error: {item['error']}\n"
    lines = []
    lines.append(f"  - **{item.get('title', 'Untitled')}**")
    if item.get("date"):
        lines.append(f"    Date: {item['date']}")
    if item.get("newspaper"):
        lines.append(f"    Newspaper: {item['newspaper']}")
    if item.get("url"):
        lines.append(f"    URL: {item['url']}")
    if item.get("description"):
        lines.append(f"    Description: {item['description']}")
    if item.get("subject"):
        subjects = item["subject"] if isinstance(item["subject"], list) else [item["subject"]]
        lines.append(f"    Subjects: {', '.join(str(s) for s in subjects[:5])}")
    if item.get("ocr_snippet"):
        lines.append(f"    Snippet: \"{item['ocr_snippet'][:200]}...\"")
    return "\n".join(lines) + "\n"


def main():
    print(f"LC Archive Search — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Running {len(SEARCHES)} searches...\n")

    lines = []
    lines.append("# LC Archive Search Results")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append(f"*{len(SEARCHES)} searches across loc.gov API and Chronicling America*")
    lines.append("")
    lines.append("---")
    lines.append("")

    current_project = None

    for entry in SEARCHES:
        label = entry[0]
        notes = entry[4]

        # Section headers
        project = "PROJECT 1" if label.startswith("1") else "PROJECT 2"
        thread = "Thread B: Nino-Dominguez" if label.startswith("1B") else \
                 "Thread A: Khan / Mohaiyuddin" if label.startswith("1A") else \
                 "What Did They Know?"

        if project != current_project:
            lines.append(f"## {project}: {'Hidden in Plain Sight' if project == 'PROJECT 1' else 'What Did They Know?'}")
            lines.append("")
            current_project = project

        print(f"Searching: {label}...")
        total, items = run_search(entry)

        status = "✅" if total > 0 else "❌"
        lines.append(f"### {status} {label}")
        lines.append(f"*{notes}*")
        lines.append(f"**Total results: {total:,}**")
        lines.append("")

        if items and "error" not in items[0]:
            lines.append(f"*Showing top {min(len(items), RESULTS_PER_QUERY)} of {total:,}:*")
            lines.append("")
            for item in items[:RESULTS_PER_QUERY]:
                lines.append(format_item(item, entry[1]))
        elif items and "error" in items[0]:
            lines.append(f"⚠️ Error: {items[0]['error']}")

        lines.append("")
        lines.append("---")
        lines.append("")

    output = "\n".join(lines)
    with open(OUTPUT_FILE, "w") as f:
        f.write(output)

    print(f"\nDone. Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
