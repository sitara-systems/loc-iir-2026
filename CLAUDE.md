# LC Archive Search — Automated Run Instructions

## What this project does

Runs targeted keyword searches against two Library of Congress APIs:
- **loc.gov API** — photos, maps, newspapers, general collections
- **Chronicling America** — full-text newspaper archive with language/date filters

Searches are organized around two concept paper proposals for the LC Innovator in Residence program (BAA 030ADV26R0021, due April 10, 2026):

1. **Hidden in Plain Sight** — Two family histories (Nino-Dominguez, Mexican-American railroad family; Khan/Mohaiyuddin, Afghan-Guyanese naturalization case) documented in LC's collections but unfindable through current discovery tools
2. **What Did They Know?** — Early federal climate science record at LC (1965 PSAC report, LBJ conservation message, USGS glacier photography)

## Your task

1. Install dependencies:
   ```
   pip install requests
   ```

2. Run the search script:
   ```
   python lc_search.py
   ```

3. The script will write two output files to this directory:
   - `LC-Search-Results.md` — full results with titles, dates, URLs, descriptions
   - `LC-Search-Summary.json` — machine-readable summary with counts per query

4. After running, **read `LC-Search-Results.md`** and do the following:
   - For each search with **total results > 0**: note the most relevant 1-2 items (title + URL)
   - For each search with **total results = 0**: note it as a gap
   - Write a brief `FINDINGS.md` summarizing:
     - Which collections confirmed relevant material (✅)
     - Which searches came up empty (❌) — these are gaps the residency addresses
     - Any unexpected finds (material we didn't know to look for)
     - 2-3 specific items (title + URL + why it's relevant) for each proposal

5. Save all output files to this directory.

## Search coverage (32 queries — v2)

### Hidden in Plain Sight — Thread B: Nino-Dominguez
- FSA/OWI photos: Mexican railroad workers Idaho, section gangs, outfit cars (fixed: uses FSA/OWI collection endpoint, not broken /photos/)
- FSA/OWI photos: Azusa CA, San Gabriel Canyon dam construction (fixed endpoint)
- Chronicling America (Spanish): repatriación/deportación 1929–1936
- Chronicling America (Spanish): ferrocarril trabajadores mexicanos 1920–1935
- Historical maps: El Paso–Idaho railroad corridor, Southern Pacific Southwest (fixed: uses railroad-maps collection)
- Congressional record: Mexican Repatriation, 1924 Act Mexican exemption
- **NEW 1B-13**: Morris Dam San Gabriel Canyon construction 1930 (oral history: Felipe bicycled to work)
- **NEW 1B-14**: Chronicling America (Spanish) La Prensa San Antonio, TX state filter, 1927–1933

### Hidden in Plain Sight — Thread A: Khan / Mohaiyuddin
- Bhagat Singh Thind Supreme Court case
- Chronicling America: Thind coverage, New York papers 1922–1924
- South Asian naturalization, British subject = white, 1910–1920
- Commissioner General Immigration Annual Reports
- Dillingham Commission report
- 1924 Act committee hearings (Johnson-Reed Act)
- **NEW 1A-08**: Direct name search — "Mohaiyuddin Khan" (naturalized Brooklyn 1919)
- **NEW 1A-09**: Direct name search — "Gool Mohamed Khan" (his father)
- **NEW 1A-10**: Chronicling America: Khan naturalization Brooklyn British Guiana 1919–1923
- **NEW 1A-11**: British Guiana immigration New York naturalization 1910–1920

### What Did They Know?
- PSAC 1965 atmospheric carbon dioxide report
- LBJ 1965 conservation/natural beauty message to Congress
- Roger Revelle congressional testimony on CO2
- USGS glacier retreat photographs
- Weather Bureau temperature records 1950s–1960s
- Chronicling America: carbon dioxide / climate warming coverage 1960–1975

## Notes

- No API key required — LC API is public
- Script is rate-limited (~1.2 sec between requests) to be respectful
- Results are **keyword searches only** — not semantic/vector search
- Goal is to confirm LC *holds* relevant material and identify catalog labels — not exhaustive research
- The full semantic search methodology is the actual IIR project; this is a preliminary proof of concept
