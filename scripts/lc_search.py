#!/usr/bin/env python3
"""
LC Archive Search — Hidden in Plain Sight + What Did They Know?
Runs targeted keyword searches against the Library of Congress API and
Chronicling America, organized by research target from LC-Research-Targets.md.

Usage:
    pip install requests
    python lc_search.py

Output:
    LC-Search-Results.md   — human-readable results with titles, dates, URLs
    LC-Search-Summary.json — machine-readable summary with counts per query

Notes:
    - No API key required; LC API is public
    - Rate-limited to ~1.2 req/sec to be respectful
    - Results are cursory keyword searches only — not vector/semantic search
    - Goal: confirm LC *does* hold relevant material and identify catalog labels
    - v2: fixed FSA/OWI searches (use collection URL, not /photos/ endpoint);
      fixed map searches (railroad-maps collection); added Mohaiyuddin Khan
      direct name searches (1A-08, 1A-09, 1A-10, 1A-11); added Morris Dam
      and La Prensa San Antonio searches (1B-13, 1B-14). Now 32 searches.
"""

import requests
import json
import time
import os
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MD   = os.path.join(DIR, "LC-Search-Results.md")
OUTPUT_JSON = os.path.join(DIR, "LC-Search-Summary.json")
DELAY = 1.2            # seconds between requests — be respectful
RESULTS_PER_QUERY = 5  # items shown per query; increase for deeper review

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "research-preview/1.0 (IIR concept paper research; contact: nathan@sitara.systems)"
})

# ── API HELPERS ─────────────────────────────────────────────────────────────

def search_loc(query, collection="search", count=RESULTS_PER_QUERY, extra_params=None):
    """Search loc.gov API. collection: 'search', 'photos', 'maps', 'newspapers', 'manuscripts'"""
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


_LANGUAGE_MAP = {
    "spa": "spanish", "eng": "english", "fre": "french", "ger": "german",
}

def search_chronicling_america(query, language=None, date1=None, date2=None,
                                state=None, count=RESULTS_PER_QUERY):
    """Search Chronicling America full-text newspaper archive via loc.gov collections API."""
    url = "https://www.loc.gov/collections/chronicling-america/"
    params = {"q": query, "fo": "json", "c": count}
    fa_filters = []
    if language:
        fa_filters.append(f"language:{_LANGUAGE_MAP.get(language, language)}")
    if state:
        fa_filters.append(f"location_state:{state.lower()}")
    if fa_filters:
        params["fa"] = "|".join(fa_filters)
    if date1 and date2:
        params["dates"] = f"{date1}/{date2}"
    elif date1:
        params["dates"] = f"{date1}/{date1}"
    try:
        r = SESSION.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def extract_loc_results(data):
    if "error" in data:
        return 0, [{"error": data["error"]}]
    total = data.get("pagination", {}).get("total", 0)
    items = []
    for r in data.get("results", []):
        desc = r.get("description", "")
        if isinstance(desc, list):
            desc = " | ".join(desc)
        items.append({
            "title":       r.get("title", "").strip(),
            "date":        r.get("date", ""),
            "url":         r.get("url", r.get("id", "")),
            "description": str(desc)[:250],
            "subject":     r.get("subject", []),
            "location":    r.get("location", []),
        })
    return total, items


def extract_ca_results(data):
    if "error" in data:
        return 0, [{"error": data["error"]}]
    total = data.get("pagination", {}).get("total", 0)
    items = []
    for r in data.get("results", []):
        desc = r.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)
        items.append({
            "title":       r.get("title", ""),
            "date":        r.get("date", ""),
            "url":         r.get("url", r.get("id", "")),
            "ocr_snippet": str(desc)[:300] if desc else "",
        })
    return total, items


# ── SEARCH PLAN ─────────────────────────────────────────────────────────────
# Format: (label, api_type, collection_or_None, kwargs_dict, notes)

SEARCHES = [

    # ════════════════════════════════════════════════════════════════════════
    # PROJECT 1: HIDDEN IN PLAIN SIGHT
    # ════════════════════════════════════════════════════════════════════════

    # ── THREAD B: Nino-Dominguez ────────────────────────────────────────────

    ("1B-01 | FSA/OWI: Mexican railroad workers, Idaho",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "mexican railroad workers idaho"},
     "Visual documentation of Mexican labor in Idaho railroad corridor"),

    ("1B-02 | FSA/OWI: Railroad section gang Southwest",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "railroad section gang southwest laborers"},
     "Section gangs = the labor category the Nino family likely falls under"),

    ("1B-03 | FSA/OWI: Railroad outfit car / labor camp",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "railroad outfit car labor camp workers"},
     "Outfit cars = the mobile homes the family lived in 1927-1930"),

    ("1B-04 | FSA/OWI: Azusa / San Gabriel Valley California",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "Azusa California labor workers"},
     "Family settled at 140 Pasadena Ave, Azusa by 1930 census"),

    ("1B-05 | FSA/OWI: San Gabriel Canyon dam construction",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "San Gabriel Canyon dam construction laborers California"},
     "Felipe Nino likely worked Morris Dam, San Gabriel Canyon, ~1930-1935"),

    ("1B-06 | Chronicling America (Spanish): Repatriación 1929-1936",
     "ca", None,
     {"query": "repatriacion mexicanos", "language": "spa",
      "date1": "1929", "date2": "1936"},
     "Spanish-language coverage of Mexican Repatriation — La Prensa, La Opinión"),

    ("1B-07 | Chronicling America (Spanish): Deportación California 1929-1936",
     "ca", None,
     {"query": "deportacion California", "language": "spa",
      "date1": "1929", "date2": "1936", "state": "California"},
     "California Spanish-language press coverage of deportation/repatriation"),

    ("1B-08 | Chronicling America (Spanish): Ferrocarril workers 1920-1935",
     "ca", None,
     {"query": "ferrocarril trabajadores mexicanos", "language": "spa",
      "date1": "1920", "date2": "1935"},
     "Spanish coverage of Mexican railroad workers"),

    ("1B-09 | Maps: El Paso to Idaho railroad corridor",
     "loc", "collections/railroad-maps-1828-to-1900",
     {"query": "railroad map El Paso Idaho Pacific"},
     "Rail corridor the family traveled — El Paso to Idaho 1927"),

    ("1B-10 | Maps: Southern Pacific Railroad Southwest",
     "loc", "collections/railroad-maps-1828-to-1900",
     {"query": "Southern Pacific Railroad map Southwest 1920"},
     "Southern Pacific operated main lines through this corridor"),

    ("1B-13 | LOC General: Morris Dam San Gabriel Canyon",
     "loc", "search",
     {"query": "Morris Dam San Gabriel Canyon construction 1930"},
     "Felipe Nino oral history says he bicycled to work — Morris Dam is the site, ~10 miles up San Gabriel Canyon from Azusa"),

    ("1B-14 | Chronicling America (Spanish): La Prensa San Antonio railroad",
     "ca", None,
     {"query": "ferrocarril trabajadores mexicanos", "language": "spa",
      "date1": "1927", "date2": "1933", "state": "Texas"},
     "La Prensa (San Antonio) was the major Spanish-language paper covering the El Paso corridor; TX state filter targets it"),

    ("1B-11 | LOC General: Mexican Repatriation congressional record",
     "loc", "search",
     {"query": "Mexican Repatriation deportation Congress 1930"},
     "Congressional debate and documentation of the Repatriation"),

    ("1B-12 | LOC General: Immigration Act 1924 Mexican exemption",
     "loc", "search",
     {"query": "Immigration Act 1924 Mexican exemption Western Hemisphere"},
     "The provision exempting Western Hemisphere from quotas — why the Nino family could cross"),

    # ── THREAD A: Khan / Mohaiyuddin ────────────────────────────────────────

    ("1A-01 | LOC General: Bhagat Singh Thind case",
     "loc", "search",
     {"query": "Bhagat Singh Thind naturalization Supreme Court"},
     "The 1923 Supreme Court case that closed the racial eligibility door"),

    ("1A-02 | Chronicling America: Thind case coverage 1922-1924",
     "ca", None,
     {"query": "Thind naturalization Hindu white", "date1": "1922", "date2": "1924"},
     "Newspaper coverage of the Thind decision — how widely reported?"),

    ("1A-03 | LOC General: South Asian naturalization British subject white",
     "loc", "search",
     {"query": "Hindu naturalization British subject white citizenship 1910 1920"},
     "The legal argument Mohaiyuddin used — British colonial status as whiteness"),

    ("1A-04 | LOC General: Commissioner General Immigration Annual Reports",
     "loc", "search",
     {"query": "Commissioner General Immigration Annual Report 1913 1919 South Asian"},
     "Annual reports document naturalization patterns — may track British Guiana / Hindu petitions"),

    ("1A-05 | LOC General: Dillingham Commission immigration report",
     "loc", "search",
     {"query": "Dillingham Commission immigration report East Indian"},
     "1910-1911 commission report that set the stage for the 1924 Act"),

    ("1A-06 | Chronicling America: British Guiana immigrants New York 1910-1925",
     "ca", None,
     {"query": "British Guiana New York immigrant", "date1": "1910", "date2": "1925"},
     "Coverage of the Indo-Caribbean community Mohaiyuddin was part of"),

    ("1A-07 | LOC General: 1924 Immigration Act committee hearings",
     "loc", "search",
     {"query": "Immigration Act 1924 House Committee hearings Johnson-Reed"},
     "Congressional hearings where racial eligibility provisions were debated"),

    ("1A-08 | LOC General: Mohaiyuddin Khan direct name search",
     "loc", "search",
     {"query": "Mohaiyuddin Khan"},
     "Direct name search — naturalized US citizen Brooklyn 1919, trader, born British Guiana 1888"),

    ("1A-09 | LOC General: Gool Mohamed Khan direct name search",
     "loc", "search",
     {"query": "Gool Mohamed Khan"},
     "Mohaiyuddin's father — may appear in immigration/trade records; family name variant"),

    ("1A-10 | Chronicling America: Khan naturalization Brooklyn 1919",
     "ca", None,
     {"query": "Khan naturalization Brooklyn British Guiana", "date1": "1919", "date2": "1923"},
     "Brooklyn naturalization court proceedings and coverage — may catch the Thind-era denaturalization wave too"),

    ("1A-11 | LOC General: British Guiana immigration New York 1910-1920",
     "loc", "search",
     {"query": "British Guiana New York immigration naturalization 1910 1919"},
     "Indo-Caribbean immigration to New York — the community Mohaiyuddin was part of; NARA coordinate to LC context"),

    # ════════════════════════════════════════════════════════════════════════
    # PROJECT 2: WHAT DID THEY KNOW?
    # ════════════════════════════════════════════════════════════════════════

    ("2-01 | LOC General: PSAC 1965 atmospheric carbon dioxide report",
     "loc", "search",
     {"query": "President Science Advisory Committee carbon dioxide atmosphere 1965"},
     "First federal acknowledgment of climate risk — the smoking gun document"),

    ("2-02 | LOC General: LBJ 1965 conservation message to Congress",
     "loc", "search",
     {"query": "Lyndon Johnson conservation natural beauty message Congress 1965"},
     "LBJ's February 1965 message to Congress explicitly mentioning atmospheric CO2"),

    ("2-03 | LOC General: Roger Revelle carbon dioxide congressional testimony",
     "loc", "search",
     {"query": "Roger Revelle carbon dioxide Congress testimony climate"},
     "Revelle testified multiple times on CO2 — key scientific witness"),

    ("2-04 | LOC Photos: USGS glacier photographs historical",
     "loc", "photos",
     {"query": "glacier retreat mountain ice historical survey"},
     "USGS historical glacier photographs documenting retreat over time"),

    ("2-05 | LOC General: Weather Bureau temperature records climate",
     "loc", "search",
     {"query": "Weather Bureau temperature climate records 1950 1960"},
     "Historical Weather Bureau climate data and reports"),

    ("2-06 | Chronicling America: Carbon dioxide climate atmosphere 1960-1975",
     "ca", None,
     {"query": "carbon dioxide atmosphere climate warming", "date1": "1960", "date2": "1975"},
     "Public press coverage of early climate science — how widely known was it?"),

    ("2-07 | LOC General: Hansen 1988 Senate testimony global warming",
     "loc", "search",
     {"query": "James Hansen Senate testimony global warming 1988"},
     "Hansen's 1988 Senate testimony is a key public moment for climate awareness"),
]

# ── RUN & OUTPUT ─────────────────────────────────────────────────────────────

def run_search(entry):
    label, api_type, collection, kwargs, notes = entry
    time.sleep(DELAY)
    if api_type == "loc":
        extra = {k: v for k, v in kwargs.items() if k != "query"}
        data = search_loc(kwargs["query"], collection=collection, extra_params=extra or None)
        return extract_loc_results(data)
    else:
        ca_kwargs = {k: v for k, v in kwargs.items()}
        query = ca_kwargs.pop("query")
        data = search_chronicling_america(query, **ca_kwargs)
        return extract_ca_results(data)


def format_item_md(item, api_type):
    if "error" in item:
        return f"  ⚠️ Error: {item['error']}\n"
    lines = [f"  - **{item.get('title', 'Untitled')}**"]
    if item.get("date"):        lines.append(f"    - Date: {item['date']}")
    if item.get("newspaper"):   lines.append(f"    - Newspaper: {item['newspaper']}")
    if item.get("url"):         lines.append(f"    - URL: <{item['url']}>")
    if item.get("description"): lines.append(f"    - Description: {item['description']}")
    if item.get("subject"):
        s = item["subject"] if isinstance(item["subject"], list) else [item["subject"]]
        lines.append(f"    - Subjects: {', '.join(str(x) for x in s[:5])}")
    if item.get("ocr_snippet"): lines.append(f"    - Snippet: \"{item['ocr_snippet'][:200]}\"")
    return "\n".join(lines) + "\n"


def main():
    print(f"LC Archive Search — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Running {len(SEARCHES)} searches...\n")

    md_lines = [
        "# LC Archive Search Results",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*{len(SEARCHES)} searches · loc.gov API + Chronicling America*",
        "", "---", "",
    ]

    summary = {"generated": datetime.now().isoformat(), "searches": []}
    current_section = None

    for entry in SEARCHES:
        label, api_type, collection, kwargs, notes = entry

        # Section headings
        section = ("## PROJECT 1: Hidden in Plain Sight\n" if label.startswith("1") else
                   "## PROJECT 2: What Did They Know?\n")
        if section != current_section:
            md_lines.append(section)
            current_section = section

        print(f"  {label}...", end=" ", flush=True)
        total, items = run_search(entry)
        status = "✅" if total > 0 else "❌"
        print(f"{status} {total:,} results")

        md_lines += [
            f"### {status} {label}",
            f"*{notes}*",
            f"**Total results in LC: {total:,}**", "",
        ]

        if items and "error" not in items[0]:
            md_lines.append(f"*Showing top {min(len(items), RESULTS_PER_QUERY)} of {total:,}:*\n")
            for item in items[:RESULTS_PER_QUERY]:
                md_lines.append(format_item_md(item, api_type))
        elif items and "error" in items[0]:
            md_lines.append(f"⚠️ {items[0]['error']}")

        md_lines += ["", "---", ""]

        summary["searches"].append({
            "label": label,
            "notes": notes,
            "api": api_type,
            "query": kwargs.get("query", ""),
            "total_results": total,
            "has_results": total > 0,
            "top_items": [
                {"title": i.get("title",""), "url": i.get("url","")}
                for i in items[:3] if "error" not in i
            ]
        })

    # Write outputs
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    found = sum(1 for s in summary["searches"] if s["has_results"])
    print(f"\nDone. {found}/{len(SEARCHES)} searches returned results.")
    print(f"  → {OUTPUT_MD}")
    print(f"  → {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
