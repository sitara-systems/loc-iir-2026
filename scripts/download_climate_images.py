"""
download_climate_images.py  v3
Downloads confirmed LC assets for both "What Did They Know?" prototypes:
  - what-did-they-know.html  (scrollytelling)
  - search-the-silence.html  (interactive search)

Strategy (in priority order per item):
  1. If a direct tile.loc.gov CDN URL is known, use it.
  2. For Chronicling America newspaper pages, use the CA page API
     (chroniclingamerica.loc.gov/lccn/{lccn}/{date}/ed-1/seq-{seq}.json)
     which returns a direct JP2/PDF URL.
  3. Otherwise, try LC's JSON metadata API (item/{id}/?fo=json) which
     returns direct image URLs and is less restrictive than the HTML pages.
  4. For external PDFs (e.g. DocumentCloud), download directly.
  5. Fall back to reporting the manual download URL.

Run on your local machine:
    pip install requests
    python download_climate_images.py

Images saved to:  ./climate-images/
"""

import os, re, time, json, sys
import requests

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "climate-images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Realistic browser headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.loc.gov/",
}


# ══════════════════════════════════════════════════════════════════════════════
# ASSET LIST — organized by prototype section
# ══════════════════════════════════════════════════════════════════════════════
#
# Naming convention:
#   N-  = Newspaper page (Chronicling America)
#   V-  = Visual / photograph (FSA, Prints & Photographs, etc.)
#   D-  = Document / report (PDF, metadata)
#
# Each entry:
#   slug          — output filename
#   description   — human label
#   section       — which prototype section uses this
#   tile_url      — direct CDN URL if known; else None
#   item_id       — LC item ID for JSON API fallback; else None
#   ca_page       — dict with lccn/date/seq for Chronicling America pages; else None
#   pdf_url       — direct PDF URL (e.g. DocumentCloud); else None
#   manual_url    — always-present fallback for manual download

ASSETS = [

    # ══════════════════════════════════════════════════════════════════════════
    #  CHAPTER I — THE ARCHIVE KNEW FIRST (1856–1958)
    #  Used by: what-did-they-know.html scrollytelling
    #           search-the-silence.html searches 1–3
    # ══════════════════════════════════════════════════════════════════════════

    # ── Eunice Newton Foote (1856) ─────────────────────────────────────────
    # No LC portrait exists. Her 1856 paper is in Public Domain Review.
    # Download the paper's first page as a stand-in visual.

    dict(
        slug="D-foote-1856-paper.pdf",
        description="Eunice Newton Foote, 'Circumstances Affecting the Heat of the Sun's Rays' (1856). First demonstration that CO2 traps heat.",
        section="ch1-foote",
        tile_url=None,
        item_id=None,
        ca_page=None,
        # BHL blocks direct PDF downloads. Use the page-image API instead:
        # https://www.biodiversitylibrary.org/pageimage/64889 (page image of the paper)
        # Or download manually from the Public Domain Review link.
        pdf_url=None,
        manual_url="https://www.biodiversitylibrary.org/item/107108#page/390/mode/1up",
    ),

    # Seneca Falls Convention — Foote was a signatory of the Declaration of Sentiments
    dict(
        slug="V-seneca-falls-declaration-sentiments.jpg",
        description="Declaration of Sentiments from the Seneca Falls Convention, 1848. Eunice Foote was among the signatories.",
        section="ch1-foote",
        tile_url=None,
        item_id="90898164",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/item/90898164/",
    ),

    # ── Early Newspapers (1910–1913) — search-the-silence search 1 ─────────
    # what-did-they-know pane-press1

    dict(
        slug="N-leon-reporter-iowa-1910-03-24.jpg",
        description="Leon Reporter (Iowa), Mar 24, 1910, p.3 — small-town Iowa paper covering CO2/atmosphere science.",
        section="ch1-press-early",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn87057096", date="1910-03-24", seq=3),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn87057096/1910-03-24/ed-1/?sp=3",
    ),
    dict(
        slug="N-san-francisco-call-1913-07-27.jpg",
        description="San Francisco Call, Jul 27, 1913, p.7 — CO2/atmosphere/warming coverage, one year after the famous 1912 coal/climate article.",
        section="ch1-press-early",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn85066387", date="1913-07-27", seq=7),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn85066387/1913-07-27/ed-1/?sp=7",
    ),

    # ── 1920s–1930s Newspapers — search-the-silence search 2 ───────────────
    # what-did-they-know pane-press1 (Seward) + pane-dust era

    dict(
        slug="N-seward-daily-gateway-alaska-1931-06-06.jpg",
        description="Seward Daily Gateway (Alaska), Jun 6, 1931, p.4 — CO2/warming science reaching small-town Alaska.",
        section="ch1-press-1930s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn87062169", date="1931-06-06", seq=4),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn87062169/1931-06-06/ed-1/?sp=4",
    ),
    dict(
        slug="N-daily-tribune-wisconsin-rapids-1933-04-12.jpg",
        description="The Daily Tribune (Wisconsin Rapids), Apr 12, 1933 — CO2/coal/warming coverage during the Dust Bowl era.",
        section="ch1-press-1930s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn86072170", date="1933-04-12", seq=1),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn86072170/1933-04-12/ed-1/?sp=1",
    ),
    dict(
        slug="N-evening-independent-st-pete-1938-09-20.jpg",
        description="Evening Independent (St. Petersburg, FL), Sep 20, 1938 — Callendar's proof that warming had begun.",
        section="ch1-press-1930s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83016278", date="1938-09-20", seq=1),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn83016278/1938-09-20/ed-1/?sp=1",
    ),

    # Also keep some of the broader early-era hits for archival completeness
    dict(
        slug="N-houston-daily-post-1898-10-23.jpg",
        description="Houston Daily Post, Oct 23, 1898, p.7 — early CO2/atmosphere keyword hit. Needs inspection.",
        section="ch1-press-early",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn86071197", date="1898-10-23", seq=7),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn86071197/1898-10-23/ed-1/?sp=7",
    ),
    dict(
        slug="N-washington-times-1918-08-25.jpg",
        description="Washington Times, Aug 25, 1918, p.26 — CO2/atmosphere keyword hit during WWI era.",
        section="ch1-press-early",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn84026749", date="1918-08-25", seq=26),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn84026749/1918-08-25/ed-1/?sp=26",
    ),

    # ── Dust Bowl Photographs — what-did-they-know pane-dust ───────────────

    dict(
        slug="V-dust-storm-cimarron-county-oklahoma.jpg",
        description="Arthur Rothstein: Farmer and sons in dust storm. Cimarron County, Oklahoma, April 1936. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id="2017760335",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017760335/",
    ),
    dict(
        slug="V-dorothea-lange-drought-refugees.jpg",
        description="Dorothea Lange: Drought refugees from Oklahoma, Blythe, California, 1936. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id="2017771280",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017771280/",
    ),
    dict(
        slug="V-dust-drifts-liberal-kansas.jpg",
        description="Dust drifts piled up near Liberal, Kansas. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id="2017759854",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017759854/",
    ),
    dict(
        slug="V-dust-drifts-barn-liberal-kansas.jpg",
        description="Dust drifts against farmer's barn near Liberal, Kansas. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id="2017759855",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017759855/",
    ),
    dict(
        slug="V-eroded-farmland-alabama.jpg",
        description="Walker Evans: Erosion near Moundville, Alabama, Summer 1936. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id="2017762044",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017762044/",
    ),
    dict(
        slug="V-tugwell-drought-committee-texas.jpg",
        description="Dr. Tugwell and Chairman Cooke of the drought committee, Texas dust bowl. FSA.",
        section="ch1-dustbowl",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/fsa.8b28198/",
    ),

    # ── Mid-Century Newspapers (1955–1965) — search-the-silence search 3 ───
    # what-did-they-know pane-star

    dict(
        slug="N-atlanta-daily-world-1956-09-01.jpg",
        description="Atlanta Daily World, Sep 1, 1956, p.6 — Black newspaper covering CO2/warming. One of only 4 press hits 1955–1965.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn82015425", date="1956-09-01", seq=6),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn82015425/1956-09-01/ed-1/?sp=6",
    ),
    dict(
        slug="N-jackson-advocate-1957-10-26.jpg",
        description="Jackson Advocate (Mississippi), Oct 26, 1957, p.2 — CO2/warming in a Black newspaper during Jim Crow.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn79000083", date="1957-10-26", seq=2),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn79000083/1957-10-26/ed-1/?sp=2",
    ),
    dict(
        slug="N-evening-star-dc-1958-01-26-mystery-warming-world.jpg",
        description="Evening Star (DC), Jan 26, 1958, p.23 — 'Mystery of the Warming World' by John Stark. THE key find.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83045462", date="1958-01-26", seq=23),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn83045462/1958-01-26/ed-1/?sp=23",
    ),
    dict(
        slug="N-evening-star-dc-1959-08-26.jpg",
        description="Evening Star (DC), Aug 26, 1959, p.7 — CO2/atmosphere/warming coverage.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83045462", date="1959-08-26", seq=7),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn83045462/1959-08-26/ed-1/?sp=7",
    ),

    # Additional Evening Star / Revelle hits (archival completeness)
    dict(
        slug="N-evening-star-dc-1955-12-27-revelle.jpg",
        description="Evening Star (DC), Dec 27, 1955 — Revelle CO2/ocean hit, before IGY.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83045462", date="1955-12-27", seq=1),
        pdf_url=None,
        manual_url="https://www.loc.gov/item/sn83045462/1955-12-27/ed-1/",
    ),
    dict(
        slug="N-evening-star-dc-1958-02-10-revelle.jpg",
        description="Evening Star (DC), Feb 10, 1958 — Revelle CO2 keyword hit during IGY.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83045462", date="1958-02-10", seq=1),
        pdf_url=None,
        manual_url="https://www.loc.gov/item/sn83045462/1958-02-10/ed-1/",
    ),
    dict(
        slug="N-evening-star-dc-1958-02-17.jpg",
        description="Evening Star (DC), Feb 17, 1958, p.12 — CO2/atmosphere, 3 weeks after 'Mystery of the Warming World'.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn83045462", date="1958-02-17", seq=12),
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/sn83045462/1958-02-17/ed-1/?sp=12",
    ),
    dict(
        slug="N-atlanta-daily-world-1960-01-28.jpg",
        description="Atlanta Daily World, Jan 28, 1960 — Revelle/CO2/climate. Black press covering climate science.",
        section="ch1-press-1950s",
        tile_url=None,
        item_id=None,
        ca_page=dict(lccn="sn82015425", date="1960-01-28", seq=1),
        pdf_url=None,
        manual_url="https://www.loc.gov/item/sn82015425/1960-01-28/ed-1/",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    #  CHAPTER II — THE GOVERNMENT CATCHES UP (1965)
    #  Used by: what-did-they-know.html pane-psac
    #           search-the-silence.html search 4
    # ══════════════════════════════════════════════════════════════════════════

    # PSAC Report — the single most important document
    dict(
        slug="D-psac-1965-restoring-quality-environment.pdf",
        description="PSAC Report: 'Restoring the Quality of Our Environment' (Nov 1965). 317 pages. The presidential warning.",
        section="ch2-psac",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url="https://www-legacy.dge.carnegiescience.edu/labs/caldeiralab/Caldeira%20downloads/PSAC,%201965,%20Restoring%20the%20Quality%20of%20Our%20Environment.pdf",
        manual_url="https://www.documentcloud.org/documents/3227654-PSAC-1965-Restoring-the-Quality-of-Our-Environment/",
    ),

    # LBJ signing / conservation context
    dict(
        slug="V-lbj-signing-ceremony.jpg",
        description="LBJ signing conservation/environmental legislation. Presidential visual context for 1965.",
        section="ch2-psac",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/photos/?q=lyndon+johnson+conservation+signing",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    #  CHAPTER III — THE SILENCE BREAKS (1988)
    #  Used by: what-did-they-know.html pane-hansen
    #           search-the-silence.html finale
    # ══════════════════════════════════════════════════════════════════════════

    # James Hansen / 1988 Senate testimony
    # No LC photograph cataloged; AP/Getty hold the press images.
    # Best LC proxy: Senate hearing room / congressional setting from era.
    dict(
        slug="V-senate-hearing-room-1980s.jpg",
        description="Senate hearing room context photo, 1980s era. Stand-in for Hansen 1988 testimony (no LC-cataloged photo of the hearing exists).",
        section="ch3-hansen",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/photos/?q=senate+hearing+room",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    #  CONTEXTUAL VISUALS — Weather Bureau, Baselines, Floods
    #  Used by: what-did-they-know.html for atmosphere/texture
    # ══════════════════════════════════════════════════════════════════════════

    dict(
        slug="V-weather-bureau-map-force-1924.jpg",
        description="Weather Bureau map force charting weather reports, c. 1924. Infrastructure of climate measurement.",
        section="visual-context",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/resource/npcc.26485/",
    ),
    dict(
        slug="V-weather-forecasting-1943.jpg",
        description="Weather forecasting at U.S. Weather Bureau, Washington DC, July 1943.",
        section="visual-context",
        tile_url=None,
        item_id="2004667470",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/item/2004667470/",
    ),
    dict(
        slug="V-hayden-survey-yellowstone-1871.jpg",
        description="William Henry Jackson: Hayden Survey party in Yellowstone, 1871. Baseline landscape before industrial warming.",
        section="visual-context",
        tile_url=None,
        item_id="2004673063",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/item/2004673063/",
    ),
    dict(
        slug="V-timothy-osullivan-wheeler-survey.jpg",
        description="Timothy O'Sullivan: Wheeler Survey, Nevada/Utah/Arizona, 1870s. The West before change.",
        section="visual-context",
        tile_url=None,
        item_id="2004662785",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/item/2004662785/",
    ),
    dict(
        slug="V-ohio-river-flood-1937.jpg",
        description="Louisville, KY during the Great Ohio River Flood, 1937.",
        section="visual-context",
        tile_url=None,
        item_id="2017762891",
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.loc.gov/pictures/item/2017762891/",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    #  CONGRESSIONAL RECORD / REFERENCE ITEMS (metadata only)
    # ══════════════════════════════════════════════════════════════════════════

    dict(
        slug="C-igy-50th-anniversary-resolution.json",
        description="H.Con.Res.189 (108th Congress): 50th anniversary of the IGY.",
        section="reference",
        tile_url=None,
        item_id=None,
        ca_page=None,
        pdf_url=None,
        manual_url="https://www.congress.gov/bill/108th-congress/house-concurrent-resolution/189",
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
#
# KEY INSIGHT: Direct JP2 and tile.loc.gov URLs often return 403.
# The solution is LC's IIIF Image API, which is their public programmatic
# access layer and is designed for exactly this use case.
#
# IIIF pattern for Chronicling America:
#   https://tile.loc.gov/image-services/iiif/
#     service:ndnp:{lccn}:{reel}:{date_seq}/full/pct:100/0/default.jpg
#
# IIIF pattern for other LC items (via JSON API → IIIF info.json):
#   {iiif_base}/full/pct:50/0/default.jpg
#

MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds


def build_ca_iiif_url(lccn: str, date: str, seq: int, pct: int = 100) -> list:
    """
    Build candidate IIIF image URLs for a Chronicling America page.
    Returns a list of URLs to try, best-first.

    Uses THREE strategies since chroniclingamerica.loc.gov now redirects:
      A) loc.gov resource JSON API  (new endpoint)
      B) chroniclingamerica.loc.gov page JSON API  (legacy, may redirect)
      C) Direct IIIF construction if we can guess the service path
    """
    candidates = []

    # ── Strategy A: New loc.gov resource JSON API ────────────────────────
    # https://www.loc.gov/resource/{lccn}/{date}/ed-1/?sp={seq}&fo=json
    resource_json_url = f"https://www.loc.gov/resource/{lccn}/{date}/ed-1/?sp={seq}&fo=json"
    try:
        r = requests.get(resource_json_url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200:
            raw = r.text
            # Find IIIF image service URLs
            iiif_matches = re.findall(
                r'https://tile\.loc\.gov/image-services/iiif/([^\s"\'<>]+?)/(?:full|info|default)',
                raw, re.IGNORECASE
            )
            for sid in iiif_matches:
                url = f"https://tile.loc.gov/image-services/iiif/{sid}/full/pct:{pct}/0/default.jpg"
                if url not in candidates:
                    candidates.append(url)

            # Find storage JP2 URLs and convert
            jp2_matches = re.findall(
                r'https://tile\.loc\.gov/storage-services/[^\s"\'<>]+\.jp2',
                raw, re.IGNORECASE
            )
            for jp2_url in jp2_matches:
                iiif_url = jp2_to_iiif(jp2_url, pct)
                if iiif_url and iiif_url not in candidates:
                    candidates.append(iiif_url)
        else:
            print(f"  ⚠ loc.gov resource API returned {r.status_code}")
    except Exception as e:
        print(f"  ⚠ loc.gov resource API failed: {e}")

    # ── Strategy B: Legacy chroniclingamerica.loc.gov JSON API ───────────
    if not candidates:
        ca_json_url = f"https://chroniclingamerica.loc.gov/lccn/{lccn}/{date}/ed-1/seq-{seq}.json"
        try:
            r = requests.get(ca_json_url, headers=HEADERS, timeout=20, allow_redirects=True)
            if r.status_code == 200:
                try:
                    data = r.json()
                except ValueError:
                    data = {}
                jp2 = data.get("jp2", "")
                if jp2:
                    iiif_url = jp2_to_iiif(jp2, pct)
                    if iiif_url:
                        candidates.append(iiif_url)
                pdf = data.get("pdf", "")
                if pdf:
                    base = pdf.rsplit(".", 1)[0]
                    iiif_url = jp2_to_iiif(base + ".jp2", pct)
                    if iiif_url:
                        candidates.append(iiif_url)
        except Exception as e:
            print(f"  ⚠ Legacy CA API failed: {e}")

    # ── Strategy C: Thumbnail (always works, low-res) ────────────────────
    thumb = f"https://chroniclingamerica.loc.gov/lccn/{lccn}/{date}/ed-1/seq-{seq}/thumbnail.jpg"
    candidates.append(thumb)

    return candidates


def jp2_to_iiif(jp2_url: str, pct: int = 100) -> str | None:
    """
    Convert a tile.loc.gov JP2 storage URL to a IIIF image API URL.

    Storage: https://tile.loc.gov/storage-services/service/ndnp/dlc/batch_.../sn83045462/1958012601/0023.jp2
    IIIF:    https://tile.loc.gov/image-services/iiif/service:ndnp:dlc:batch_...:sn83045462:1958012601:0023/full/pct:100/0/default.jpg
    """
    if not jp2_url or "tile.loc.gov" not in jp2_url:
        return None

    # Extract the path after /storage-services/ or /image-services/
    match = re.search(r'tile\.loc\.gov/storage-services/(.+?)\.jp2', jp2_url, re.IGNORECASE)
    if not match:
        # Maybe it's already an image-services path
        match = re.search(r'tile\.loc\.gov/image-services/iiif/(.+?)/', jp2_url, re.IGNORECASE)
        if match:
            service_id = match.group(1)
            return f"https://tile.loc.gov/image-services/iiif/{service_id}/full/pct:{pct}/0/default.jpg"
        return None

    # Convert path separators: service/ndnp/dlc/... → service:ndnp:dlc:...
    path = match.group(1)
    service_id = path.replace("/", ":")

    return f"https://tile.loc.gov/image-services/iiif/{service_id}/full/pct:{pct}/0/default.jpg"


def fetch_item_image_urls(item_id: str) -> list:
    """
    Hit LC's JSON metadata API for an item and return candidate image URLs.
    Prioritizes IIIF URLs over direct tile/storage URLs.
    """
    url = f"https://www.loc.gov/item/{item_id}/?fo=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ✗ JSON API failed: {e}")
        return []

    iiif_urls = []
    raw_urls = []

    # Path 1: resources[].files[][] — look for IIIF URLs first, then raw
    for resource in data.get("resources", []):
        for file_group in resource.get("files", []):
            for f in file_group:
                if isinstance(f, dict):
                    u = f.get("url", "")
                    if not u:
                        continue
                    # Prefer IIIF image-services URLs
                    if "image-services/iiif" in u:
                        iiif_urls.append(u)
                    elif any(u.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".tif", ".tiff")):
                        raw_urls.append(u)

    # Path 2: item.image_url (often IIIF-compatible)
    item_block = data.get("item", {})
    for u in item_block.get("image_url", []):
        if "image-services/iiif" in u:
            iiif_urls.append(u)
        elif u not in raw_urls:
            raw_urls.append(u)

    # Path 3: Look for IIIF info URLs and construct download URLs
    raw = json.dumps(data)

    # Find IIIF image service identifiers
    iiif_matches = re.findall(
        r'https://tile\.loc\.gov/image-services/iiif/([^\s"\'<>]+?)/(?:full|info)',
        raw, re.IGNORECASE
    )
    for service_id in iiif_matches:
        candidate = f"https://tile.loc.gov/image-services/iiif/{service_id}/full/pct:100/0/default.jpg"
        if candidate not in iiif_urls:
            iiif_urls.append(candidate)

    # Find storage JP2 URLs and convert to IIIF
    jp2_matches = re.findall(
        r'https://tile\.loc\.gov/storage-services/[^\s"\'<>]+\.jp2',
        raw, re.IGNORECASE
    )
    for jp2_url in jp2_matches:
        iiif_url = jp2_to_iiif(jp2_url)
        if iiif_url and iiif_url not in iiif_urls:
            iiif_urls.append(iiif_url)

    # Return IIIF URLs first (they won't 403), then raw URLs as fallback
    return iiif_urls + raw_urls


def fetch_resource_iiif(manual_url: str) -> list:
    """
    For items specified by a /resource/, /pictures/, or /item/ URL,
    hit the LC JSON API to find IIIF image URLs.
    Returns a list of candidate URLs to try.
    """
    candidates = []

    # Normalize to JSON API endpoint
    # /resource/fsa.8b28198/          → ?fo=json
    # /pictures/item/2017760335/      → ?fo=json
    # /item/2004667470/               → ?fo=json
    # /photos/?q=...                  → skip (search URL, can't resolve)
    if "?q=" in manual_url or "/photos/?" in manual_url:
        return candidates

    base = manual_url.rstrip("/")
    # Remove any existing query params
    if "?" in base:
        base = base.split("?")[0]
    json_url = base + "?fo=json"

    # Ensure it has a host
    if not json_url.startswith("http"):
        json_url = "https://www.loc.gov" + json_url

    try:
        r = requests.get(json_url, headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            print(f"  ⚠ JSON API returned {r.status_code}")
            return candidates
        raw = r.text
    except Exception as e:
        print(f"  ✗ Resource JSON API failed: {e}")
        return candidates

    # Look for IIIF image service URLs
    iiif_matches = re.findall(
        r'https://tile\.loc\.gov/image-services/iiif/([^\s"\'<>]+?)/(?:full|info|default)',
        raw, re.IGNORECASE
    )
    for sid in iiif_matches:
        url = f"https://tile.loc.gov/image-services/iiif/{sid}/full/pct:100/0/default.jpg"
        if url not in candidates:
            candidates.append(url)

    # Look for storage JP2s and convert to IIIF
    jp2_matches = re.findall(
        r'https://tile\.loc\.gov/storage-services/[^\s"\'<>]+\.jp2',
        raw, re.IGNORECASE
    )
    for jp2_url in jp2_matches:
        iiif_url = jp2_to_iiif(jp2_url)
        if iiif_url and iiif_url not in candidates:
            candidates.append(iiif_url)

    # Look for direct image URLs (some items serve JPEGs directly)
    img_matches = re.findall(
        r'https://tile\.loc\.gov/[^\s"\'<>]+\.(?:jpg|jpeg)',
        raw, re.IGNORECASE
    )
    for img_url in img_matches:
        if img_url not in candidates:
            candidates.append(img_url)

    return candidates


def download(url: str, dest: str, retries: int = MAX_RETRIES) -> bool:
    """Download a URL to a local file with retry logic."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=120, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as fh:
                for chunk in r.iter_content(65536):
                    fh.write(chunk)
            kb = os.path.getsize(dest) // 1024
            if kb < 1:
                # Suspiciously small — might be an error page
                os.remove(dest)
                print(f"  ✗ File too small ({kb} KB), likely an error page")
                return False
            print(f"  ✓ {kb:,} KB  →  {os.path.basename(dest)}")
            return True
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            if os.path.exists(dest):
                os.remove(dest)
            if status == 403 and attempt < retries:
                print(f"  ⚠ 403 on attempt {attempt+1}, retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
                continue
            elif status == 429 and attempt < retries:
                wait = RETRY_DELAY * (attempt + 2)
                print(f"  ⚠ 429 rate-limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"  ✗ HTTP {status}: {e}")
                return False
        except Exception as e:
            if os.path.exists(dest):
                os.remove(dest)
            print(f"  ✗ Download failed: {e}")
            return False
    return False


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    ok, fail = 0, 0
    manual = []

    # Separate downloadable images/PDFs from reference-only items
    downloadable = [a for a in ASSETS if not a["slug"].endswith(".json")]
    json_items = [a for a in ASSETS if a["slug"].endswith(".json")]

    # Count by section for a nice summary
    sections = {}
    for a in ASSETS:
        sections.setdefault(a["section"], []).append(a["slug"])

    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  What Did They Know? — Asset Downloader v3              ║")
    print(f"╠══════════════════════════════════════════════════════════╣")
    print(f"║  {len(downloadable):2d} downloadable assets                              ║")
    print(f"║  {len(json_items):2d} reference-only items                              ║")
    print(f"║  Output: {OUTPUT_DIR:<46s} ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print()

    print("Sections:")
    for sec, slugs in sections.items():
        print(f"  {sec:24s}  {len(slugs)} items")
    print()

    for a in downloadable:
        slug = a["slug"]
        dest = os.path.join(OUTPUT_DIR, slug)

        # Skip files that already exist and are non-trivially sized (> 5 KB)
        if os.path.exists(dest) and os.path.getsize(dest) > 5120:
            print(f"✓ {slug}  (already exists, {os.path.getsize(dest)//1024:,} KB — skipping)")
            ok += 1
            print()
            continue

        print(f"→ {slug}")
        desc = a['description']
        print(f"  {desc[:100]}{'...' if len(desc) > 100 else ''}")

        downloaded = False

        # ── Strategy 1: Direct tile URL (pre-known, rare) ────────────────
        if a.get("tile_url"):
            print(f"  [1] Direct tile URL")
            downloaded = download(a["tile_url"], dest)

        # ── Strategy 2: Chronicling America → IIIF ───────────────────────
        if not downloaded and a.get("ca_page"):
            ca = a["ca_page"]
            print(f"  [2] CA IIIF → {ca['lccn']}/{ca['date']}/seq-{ca['seq']}")
            ca_urls = build_ca_iiif_url(ca["lccn"], ca["date"], ca["seq"], pct=100)
            for url in ca_urls:
                kind = "IIIF" if "image-services" in url else "thumb" if "thumbnail" in url else "direct"
                print(f"  [{kind}] {url[:90]}...")
                downloaded = download(url, dest)
                if downloaded:
                    break
                # If IIIF full-res 403s, try 50% before moving to next candidate
                if not downloaded and "pct:100" in url:
                    half_url = url.replace("pct:100", "pct:50")
                    print(f"  [IIIF 50%] retrying at half scale...")
                    downloaded = download(half_url, dest)
                    if downloaded:
                        break
                time.sleep(0.5)

        # ── Strategy 3: Direct PDF URL ───────────────────────────────────
        if not downloaded and a.get("pdf_url"):
            print(f"  [3] Direct PDF download")
            downloaded = download(a["pdf_url"], dest)

        # ── Strategy 4: LC JSON API → IIIF ───────────────────────────────
        if not downloaded and a.get("item_id"):
            print(f"  [4] JSON API → item/{a['item_id']}")
            candidates = fetch_item_image_urls(a["item_id"])
            if candidates:
                for i, url in enumerate(candidates[:4]):  # try up to 4
                    kind = "IIIF" if "image-services/iiif" in url else "direct"
                    print(f"  [{kind}] {url[:85]}...")
                    downloaded = download(url, dest)
                    if downloaded:
                        break
                    time.sleep(0.5)
            else:
                print(f"  ✗ No image URLs from JSON API")

        # ── Strategy 5: Resource/pictures/item URL → IIIF ──────────────
        # For items with only a manual_url like /resource/fsa.8b28198/
        if not downloaded and not a.get("ca_page") and not a.get("item_id") and not a.get("pdf_url"):
            manual_url = a.get("manual_url", "")
            if any(p in manual_url for p in ["/resource/", "/pictures/", "/item/"]):
                print(f"  [5] Manual URL → IIIF lookup")
                iiif_urls = fetch_resource_iiif(manual_url)
                for url in iiif_urls[:4]:
                    kind = "IIIF" if "image-services" in url else "direct"
                    print(f"  [{kind}] {url[:90]}...")
                    downloaded = download(url, dest)
                    if downloaded:
                        break
                    time.sleep(0.5)

        # ── Tally ────────────────────────────────────────────────────────
        if downloaded:
            ok += 1
        else:
            fail += 1
            manual.append(a)

        time.sleep(1.0)  # polite delay between items
        print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"{'─'*60}")
    print(f"Done.  {ok} downloaded  ·  {fail} need manual download")
    print()

    if manual:
        print("┌──────────────────────────────────────────────────────────┐")
        print("│  MANUAL DOWNLOAD NEEDED                                  │")
        print("│  Visit the URL, click the download icon, and save to:    │")
        print(f"│  {OUTPUT_DIR:<54s}  │")
        print("└──────────────────────────────────────────────────────────┘")
        print()
        for a in manual:
            print(f"  {a['slug']}")
            print(f"  → {a['manual_url']}")
            print()

    if json_items:
        print("Congressional/catalog reference items (visit in browser):")
        print()
        for a in json_items:
            print(f"  {a['slug'].replace('.json', '')}")
            print(f"  → {a['manual_url']}")
            print()

    # Write a manifest for easy reference
    manifest_path = os.path.join(OUTPUT_DIR, "_manifest.json")
    manifest = []
    for a in ASSETS:
        entry = {
            "slug": a["slug"],
            "description": a["description"],
            "section": a["section"],
            "manual_url": a["manual_url"],
            "downloaded": os.path.exists(os.path.join(OUTPUT_DIR, a["slug"])),
        }
        manifest.append(entry)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
