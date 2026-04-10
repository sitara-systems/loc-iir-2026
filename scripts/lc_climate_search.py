#!/usr/bin/env python3
"""
LC Climate Search — What Did They Know?
Runs targeted keyword searches against the Library of Congress API and
Chronicling America, organized by the evidence chain in the climate
knowledge chronology (1856–1992).

Usage:
    pip install requests
    python lc_climate_search.py

Output:
    Climate-Search-Results.md   — human-readable results with titles, dates, URLs
    Climate-Search-Summary.json — machine-readable summary with counts per query

Notes:
    - No API key required; LC API is public
    - Rate-limited to ~1.2 req/sec to be respectful
    - Results are cursory keyword searches only — not vector/semantic search
    - Goal: confirm LC holds relevant material, identify catalog labels,
      find specific items for the concept paper and prototype
"""

import requests
import json
import time
import os
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────

DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MD   = os.path.join(DIR, "Climate-Search-Results.md")
OUTPUT_JSON = os.path.join(DIR, "Climate-Search-Summary.json")
DELAY = 1.2            # seconds between requests — be respectful
RESULTS_PER_QUERY = 5  # items shown per query; increase for deeper review

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "research-preview/1.0 (IIR concept paper research; contact: nathan@sitara.systems)"
})

# ── API HELPERS ─────────────────────────────────────────────────────────────

def search_loc(query, collection="search", count=RESULTS_PER_QUERY, extra_params=None):
    """Search loc.gov API. collection: 'search', 'photos', 'maps', etc."""
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
#
# Organized chronologically by the evidence chain:
#   ERA 1: Early Science (1856–1938)
#   ERA 2: Mid-Century Knowledge (1950s–1965)
#   ERA 3: The Warning (1965 PSAC report)
#   ERA 4: The Silence (1966–1987)
#   ERA 5: The Reckoning (1988–1992)
#   VISUAL: Landscape / environmental change photography
#   META: Discovery gaps and press silence

SEARCHES = [

    # ════════════════════════════════════════════════════════════════════════
    # ERA 1: EARLY SCIENCE (1856–1938)
    # The foundational papers — did LC catalog the science?
    # ════════════════════════════════════════════════════════════════════════

    ("E1-01 | LOC General: Eunice Foote 1856 CO2 heat experiments",
     "loc", "search",
     {"query": "Eunice Foote heat sun rays gas 1856"},
     "First demonstration that CO2 traps heat — her paper was read by a man at AAAS because she couldn't present"),

    ("E1-02 | LOC General: Eunice Newton Foote women's rights science",
     "loc", "search",
     {"query": "Eunice Newton Foote scientist women"},
     "Foote was also a women's rights activist (Seneca Falls signatory) — LC may hold her through that door"),

    ("E1-03 | LOC General: American Journal of Science 1856",
     "loc", "search",
     {"query": "American Journal Science Arts 1856"},
     "The journal that published Foote's paper — confirm LC holds this volume"),

    ("E1-04 | LOC General: Svante Arrhenius carbon dioxide temperature 1896",
     "loc", "search",
     {"query": "Arrhenius carbonic acid temperature climate"},
     "First quantitative climate sensitivity estimate (1896) — Philosophical Magazine"),

    ("E1-05 | LOC General: Guy Callendar 1938 carbon dioxide temperature",
     "loc", "search",
     {"query": "Callendar carbon dioxide temperature artificial production"},
     "British engineer who proved CO2 was measurably rising — used US Weather Bureau data"),

    ("E1-06 | Chronicling America: coal smoke climate atmosphere 1890-1915",
     "ca", None,
     {"query": "coal smoke atmosphere climate temperature",
      "date1": "1890", "date2": "1915"},
     "Early newspaper coverage linking coal combustion to atmospheric effects — the 1912 coal/climate article is famous"),

    ("E1-07 | Chronicling America: carbon dioxide atmosphere 1896-1940",
     "ca", None,
     {"query": "carbon dioxide atmosphere temperature warming",
      "date1": "1896", "date2": "1940"},
     "Press coverage of Arrhenius/Callendar era — how visible was early climate science?"),

    # ════════════════════════════════════════════════════════════════════════
    # ERA 2: MID-CENTURY KNOWLEDGE (1950s–1964)
    # Revelle, Keeling, International Geophysical Year
    # ════════════════════════════════════════════════════════════════════════

    ("E2-01 | LOC General: Roger Revelle carbon dioxide ocean 1957",
     "loc", "search",
     {"query": "Roger Revelle carbon dioxide ocean atmosphere geophysical"},
     "Revelle-Suess paper (1957) — 'human beings are now carrying out a large scale geophysical experiment'"),

    ("E2-02 | LOC General: International Geophysical Year 1957 Congress",
     "loc", "search",
     {"query": "International Geophysical Year 1957 Congress appropriations"},
     "Congressional funding/oversight of IGY — which launched the Keeling measurements"),

    ("E2-03 | LOC General: Charles Keeling carbon dioxide measurements Mauna Loa",
     "loc", "search",
     {"query": "Keeling carbon dioxide Mauna Loa measurements atmosphere"},
     "Keeling Curve — the foundational CO2 dataset, begun during IGY 1958"),

    ("E2-04 | LOC General: Revelle congressional testimony climate CO2",
     "loc", "search",
     {"query": "Revelle testimony Congress carbon dioxide climate"},
     "Revelle testified before Congress on CO2/oceans — this should be in committee hearing records"),

    ("E2-05 | Chronicling America: carbon dioxide atmosphere 1955-1965",
     "ca", None,
     {"query": "carbon dioxide atmosphere warming scientist",
      "date1": "1955", "date2": "1965"},
     "Press coverage during the decade leading up to the PSAC report — was the public aware?"),

    ("E2-06 | LOC General: Conservation Foundation 1963 CO2 conference",
     "loc", "search",
     {"query": "Conservation Foundation carbon dioxide conference 1963"},
     "The 1963 conference where Revelle and Keeling presented — precursor to the PSAC panel"),

    # ════════════════════════════════════════════════════════════════════════
    # ERA 3: THE WARNING (1965)
    # PSAC report + LBJ message — the central documents
    # ════════════════════════════════════════════════════════════════════════

    ("E3-01 | LOC General: PSAC 1965 Restoring Quality Environment",
     "loc", "search",
     {"query": "President Science Advisory Committee Restoring Quality Environment 1965"},
     "THE central document — 317 pages, 22-page CO2 appendix, chaired by Revelle, given to LBJ"),

    ("E3-02 | LOC General: PSAC atmospheric carbon dioxide appendix Y",
     "loc", "search",
     {"query": "Science Advisory Committee atmospheric carbon dioxide appendix environmental pollution"},
     "Alternate search terms for the PSAC report's CO2 section (Appendix Y4)"),

    ("E3-03 | LOC General: LBJ conservation natural beauty Congress 1965",
     "loc", "search",
     {"query": "Johnson conservation natural beauty message Congress 1965"},
     "LBJ Special Message to Congress on Conservation (Feb 8, 1965) — accompanied the PSAC report"),

    ("E3-04 | LOC General: LBJ pollution environment special message 1965",
     "loc", "search",
     {"query": "Johnson pollution environment special message 1965 quality"},
     "Alternate search — LBJ's messages to Congress about environmental quality"),

    ("E3-05 | Chronicling America: Johnson conservation environment 1965",
     "ca", None,
     {"query": "Johnson conservation environment pollution message",
      "date1": "1965", "date2": "1965"},
     "Newspaper coverage of LBJ's environmental message — was the PSAC warning reported?"),

    ("E3-06 | LOC General: Environmental Pollution Panel 1965 report",
     "loc", "search",
     {"query": "Environmental Pollution Panel report 1965"},
     "The PSAC sub-panel's formal name — may be cataloged under this title"),

    # ════════════════════════════════════════════════════════════════════════
    # ERA 4: THE SILENCE (1966–1987)
    # What happened between the warning and the reckoning?
    # ════════════════════════════════════════════════════════════════════════

    ("E4-01 | LOC General: Clean Air Act 1970 Senate hearings pollution",
     "loc", "search",
     {"query": "Clean Air Act 1970 Senate hearings air pollution"},
     "The Clean Air Act addressed smog but not CO2 — the specific mechanism of sidelining"),

    ("E4-02 | LOC General: National Academy Sciences climate 1979 Charney",
     "loc", "search",
     {"query": "National Academy Sciences climate carbon dioxide 1979"},
     "The Charney Report (1979) — first NAS climate sensitivity assessment; 1.5–4.5°C range still holds"),

    ("E4-03 | LOC General: EPA carbon dioxide climate assessment 1983",
     "loc", "search",
     {"query": "EPA carbon dioxide climate assessment greenhouse 1983"},
     "EPA's 1983 report 'Can We Delay a Greenhouse Warming?' — another federal warning ignored"),

    ("E4-04 | Chronicling America: carbon dioxide greenhouse warming 1970-1987",
     "ca", None,
     {"query": "carbon dioxide greenhouse warming climate",
      "date1": "1970", "date2": "1987"},
     "Press coverage between the warning and the reckoning — the two decades of institutional silence"),

    ("E4-05 | LOC General: Earth Day 1970 environment Congress",
     "loc", "search",
     {"query": "Earth Day 1970 environment Congress pollution"},
     "Earth Day (April 22, 1970) — mass public environmentalism that focused on visible pollution, not CO2"),

    ("E4-06 | Chronicling America: Earth Day 1970 newspaper coverage",
     "ca", None,
     {"query": "Earth Day environment pollution April",
      "date1": "1970", "date2": "1970"},
     "Newspaper coverage of the first Earth Day — what environmental concerns were visible to the public?"),

    ("E4-07 | LOC General: ozone layer CFC Montreal Protocol Congress",
     "loc", "search",
     {"query": "ozone layer chlorofluorocarbon Montreal Protocol Congress hearings"},
     "The ozone story — the one time the system worked (science → warning → international treaty)"),

    # ════════════════════════════════════════════════════════════════════════
    # ERA 5: THE RECKONING (1988–1992)
    # Hansen testimony, IPCC, Rio
    # ════════════════════════════════════════════════════════════════════════

    ("E5-01 | LOC General: Hansen 1988 Senate testimony global warming",
     "loc", "search",
     {"query": "James Hansen Senate testimony global warming 1988"},
     "The 1988 testimony that put climate change on the political map"),

    ("E5-02 | LOC General: Senate Energy Natural Resources 1988 hearing",
     "loc", "search",
     {"query": "Senate Energy Natural Resources Committee hearing 1988 climate greenhouse"},
     "The committee record for the hearing — Tim Wirth's famous staging (opening windows to make the room hot)"),

    ("E5-03 | Chronicling America: global warming greenhouse 1988",
     "ca", None,
     {"query": "global warming greenhouse effect climate",
      "date1": "1988", "date2": "1988"},
     "1988 press coverage — Hansen testimony hit front page of NYT; how widely did it ripple?"),

    ("E5-04 | LOC General: IPCC First Assessment Report 1990 Congress",
     "loc", "search",
     {"query": "IPCC Intergovernmental Panel Climate Change 1990 assessment Congress"},
     "First IPCC report (1990) — the international scientific consensus transmitted to policymakers"),

    ("E5-05 | LOC General: Rio Earth Summit UNFCCC 1992 Congress",
     "loc", "search",
     {"query": "Rio Earth Summit climate convention UNFCCC 1992 Congress treaty"},
     "Rio de Janeiro Earth Summit (1992) — the first international climate treaty, ratified by the Senate"),

    # ════════════════════════════════════════════════════════════════════════
    # VISUAL: LANDSCAPE / ENVIRONMENTAL CHANGE PHOTOGRAPHY
    # FSA/OWI, USGS surveys, coastal surveys
    # ════════════════════════════════════════════════════════════════════════

    ("V-01 | FSA/OWI: Dust Bowl erosion drought Oklahoma Kansas",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "dust bowl erosion drought Oklahoma Kansas"},
     "FSA Dust Bowl documentation — environmental devastation as a preview of climate-driven landscape change"),

    ("V-02 | FSA/OWI: Dust storm farmer Plains wind erosion",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "dust storm farmer Plains wind erosion"},
     "Arthur Rothstein's iconic Dust Bowl images — LC's strongest visual climate-adjacent material"),

    ("V-03 | FSA/OWI: drought California farmworker water",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "drought California farmworker water irrigation"},
     "Western drought photography — water scarcity documentation"),

    ("V-04 | Photos: USGS glacier mountain ice survey historical",
     "loc", "photos",
     {"query": "glacier mountain ice retreat survey photograph"},
     "USGS glacier photographs — the most powerful visual evidence of long-term climate change"),

    ("V-05 | Photos: Hayden Wheeler King survey landscape 1870 1880",
     "loc", "photos",
     {"query": "Hayden survey Wheeler survey landscape mountain photograph"},
     "Great Surveys of the West (1870s) — baseline landscape photographs from before warming"),

    ("V-06 | Maps: coastal survey United States 1880 1900 shoreline",
     "loc", "maps",
     {"query": "coast survey United States shoreline chart 1880 1900"},
     "US Coast and Geodetic Survey maps — 160 years of coastline documentation, evidence of sea level change"),

    ("V-07 | Photos: Weather Bureau instruments meteorological station",
     "loc", "photos",
     {"query": "Weather Bureau meteorological station instruments"},
     "Photographs of the infrastructure of climate measurement — the institutional record"),

    ("V-08 | FSA/OWI: flood river damage 1936 1937 1938",
     "loc", "collections/fsa-owi-black-and-white-negatives",
     {"query": "flood river damage destruction 1936 1937 1938"},
     "Great Flood photography — extreme weather events documented during the Dust Bowl era"),

    # ════════════════════════════════════════════════════════════════════════
    # META: DISCOVERY GAPS AND PRESS SILENCE
    # Searches designed to measure what's *absent*
    # ════════════════════════════════════════════════════════════════════════

    ("M-01 | Chronicling America: carbon dioxide climate 1960-1975 (silence test)",
     "ca", None,
     {"query": "carbon dioxide atmosphere climate warming",
      "date1": "1960", "date2": "1975"},
     "THE key negative finding — v1 returned only 1 result across 15 years. The knowledge gap."),

    ("M-02 | Chronicling America: greenhouse effect 1960-1987 (awareness test)",
     "ca", None,
     {"query": "greenhouse effect warming atmosphere",
      "date1": "1960", "date2": "1987"},
     "When did 'greenhouse effect' enter public discourse? Measuring the lag between science and press."),

    ("M-03 | Chronicling America: global warming 1970-1987 (term emergence)",
     "ca", None,
     {"query": "global warming",
      "date1": "1970", "date2": "1987"},
     "When did 'global warming' as a phrase appear in newspapers? Before or after Hansen 1988?"),

    ("M-04 | Chronicling America: global warming 1988-1990 (post-Hansen)",
     "ca", None,
     {"query": "global warming",
      "date1": "1988", "date2": "1990"},
     "Post-Hansen press explosion — contrast with pre-1988 silence to measure the inflection point"),

    ("M-05 | LOC General: Exxon climate change internal research",
     "loc", "search",
     {"query": "Exxon climate change internal research fossil fuel industry"},
     "Industry knowledge — the 'they' in 'What Did They Know?' includes the private sector"),

    ("M-06 | LOC General: American Petroleum Institute climate carbon 1959",
     "loc", "search",
     {"query": "American Petroleum Institute climate carbon dioxide"},
     "Edward Teller warned the API about CO2 in 1959 — LC may hold industry testimony or trade press"),
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
    if item.get("url"):         lines.append(f"    - URL: <{item['url']}>")
    if item.get("description"): lines.append(f"    - Description: {item['description']}")
    if item.get("subject"):
        s = item["subject"] if isinstance(item["subject"], list) else [item["subject"]]
        lines.append(f"    - Subjects: {', '.join(str(x) for x in s[:5])}")
    if item.get("ocr_snippet"): lines.append(f"    - Snippet: \"{item['ocr_snippet'][:200]}\"")
    return "\n".join(lines) + "\n"


def main():
    print(f"LC Climate Search — What Did They Know?")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Running {len(SEARCHES)} searches...\n")

    md_lines = [
        "# LC Climate Search Results — What Did They Know?",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*{len(SEARCHES)} searches · loc.gov API + Chronicling America*",
        "", "---", "",
    ]

    summary = {"generated": datetime.now().isoformat(), "searches": []}
    current_era = None

    era_headers = {
        "E1": "## ERA 1: Early Science (1856–1938)\n",
        "E2": "## ERA 2: Mid-Century Knowledge (1950s–1964)\n",
        "E3": "## ERA 3: The Warning (1965)\n",
        "E4": "## ERA 4: The Silence (1966–1987)\n",
        "E5": "## ERA 5: The Reckoning (1988–1992)\n",
        "V":  "## VISUAL: Landscape & Environmental Change Photography\n",
        "M":  "## META: Discovery Gaps and Press Silence\n",
    }

    for entry in SEARCHES:
        label, api_type, collection, kwargs, notes = entry

        # Section headings
        era_key = label.split("-")[0]
        if era_key != current_era:
            md_lines.append(era_headers.get(era_key, f"## {era_key}\n"))
            current_era = era_key

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

    # Quick stats
    era_stats = {}
    for s in summary["searches"]:
        era = s["label"].split("-")[0]
        era_stats.setdefault(era, {"total": 0, "found": 0})
        era_stats[era]["total"] += 1
        if s["has_results"]:
            era_stats[era]["found"] += 1

    print(f"\nResults by era:")
    era_names = {
        "E1": "Early Science", "E2": "Mid-Century", "E3": "The Warning",
        "E4": "The Silence", "E5": "The Reckoning", "V": "Visual",
        "M": "Meta/Gaps"
    }
    for era, stats in era_stats.items():
        name = era_names.get(era, era)
        print(f"  {name}: {stats['found']}/{stats['total']} returned results")


if __name__ == "__main__":
    main()
