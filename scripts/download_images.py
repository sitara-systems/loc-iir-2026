"""
download_images.py  v2
Downloads confirmed LC/FSA assets for the Hidden in Plain Sight proposal.

Strategy (in priority order per item):
  1. If a direct tile.loc.gov CDN URL is known, use it.
  2. Otherwise, try LC's JSON metadata API (item/{id}/?fo=json) which
     returns direct image URLs and is less restrictive than the HTML pages.
  3. Fall back to reporting the manual download URL.

Run on your local machine:
    pip install requests
    python download_images.py

Images saved to:  ./proposal-images/
"""

import os, re, time, json
import requests

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "proposal-images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Realistic browser headers — avoids most bot detection
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

# ── ASSET LIST ───────────────────────────────────────────────────────────────
# Each entry:
#   slug          — output filename
#   description   — human label
#   tile_url      — direct CDN URL if known (fastest, most reliable); else None
#   item_id       — LC item ID for JSON API fallback; else None
#   manual_url    — always-present fallback for manual download

ASSETS = [

    # Thread B: Nino-Dominguez ─────────────────────────────────────────────

    dict(
        slug="1B-nino-el-paso-crossing.jpg",
        description="Inspecting a freight train from Mexico, El Paso (FSA)",
            tile_url=None,
        item_id=None,
        manual_url="https://www.loc.gov/resource/fsa.8b32380/",
    ),
    dict(
        slug="1B-nino-section-gang-california.jpg",
        description="Dorothea Lange: White section gang, King City CA — 'Before the depression this work was done entirely by Mexican labor'",
        tile_url=None,
        item_id=None,
        manual_url="https://www.loc.gov/resource/fsa.8b31851/",
    ),
    dict(
        slug="1B-nino-atsf-section-gang-needles.jpg",
        description="Jack Delano: Indian section gang, ATSF Railroad yards, Needles CA — exact railroad system the family traveled",
        tile_url=None,
        item_id="2017849017",
        manual_url="https://www.loc.gov/item/2017849017/",
    ),
    dict(
        slug="1B-nino-morris-dam-hoover-dedication.jpg",
        description="Herbert Hoover dedicates Morris Dam near Pasadena, Cal., ca. 1934 — the dam Felipe Nino bicycled to work on",
        tile_url=None,
        item_id="2008675670",
        manual_url="https://www.loc.gov/item/2008675670/",
    ),

    # Thread B: Mexico origin story ───────────────────────────────────────

    dict(
        slug="1B-mexico-adobe-brick-1920.jpg",
        description="Making adobe brick and drying them in the sun, Mexico — Keystone View Co., 1920. Socorro's father's industry, photographed while the family was in Uriangato.",
        tile_url=None,
        item_id="2020639554",
        manual_url="https://www.loc.gov/item/2020639554/",
    ),
    dict(
        slug="1B-mexico-adobe-brick-1926.jpg",
        description="Making brick by hand in Mexico — Keystone View Co., 1926. Same year the Cristero War begins and Calles Law passes. The year before the family crossed.",
        tile_url=None,
        item_id="2020639555",
        manual_url="https://www.loc.gov/item/2020639555/",
    ),
    dict(
        slug="1B-guanajuato-city-view.jpg",
        description="Guanajuato, Mexico — Detroit Publishing Co., ca. 1900s. The city and state where the Dominguez family lived.",
        tile_url=None,
        item_id="2016797074",
        manual_url="https://www.loc.gov/item/2016797074/",
    ),

    # Thread A: Khan family — origin and world ────────────────────────────

    dict(
        slug="1A-calcutta-harrison-road-1.jpg",
        description="Calcutta. Harrison Road. I. — Photoglob Co., ca. 1890. Commercial Calcutta where the Khan family built their trading business.",
        tile_url=None,
        item_id="2017658176",
        manual_url="https://www.loc.gov/item/2017658176/",
    ),
    dict(
        slug="1A-calcutta-harrison-road-2.jpg",
        description="Calcutta. Harrison Road. II. — Photoglob Co., ca. 1890. Streets, ox teams, vending stands. The trading district the family operated in.",
        tile_url=None,
        item_id="2017658177",
        manual_url="https://www.loc.gov/item/2017658177/",
    ),
    dict(
        slug="1A-british-guiana-illustrated-history.jpg",
        description="An Illustrated History of British Guiana, 1866 — 265 mounted photographs of Georgetown. The colonial world Gool Mohamed Khan arrived into in 1877.",
        tile_url=None,
        item_id="01019998",
        manual_url="https://www.loc.gov/pictures/item/01019998/",
    ),
    # NOTE: The Races of Afghanistan (1880) — loc.gov/resource/gdclccn.05003058/ — is a
    # digitized book. Navigate to it manually, go to the Yusufzai chapter (approx. pp. 50–80),
    # and screenshot the portrait illustrations. These show the exact ethnic group (Yusufzai
    # Pathan) that Gool Mohamed Khan belonged to — colonial classification in book form.
    # Manual URL: https://www.loc.gov/resource/gdclccn.05003058/

    # Thread A: Khan / Mohaiyuddin ─────────────────────────────────────────

    dict(
        slug="1A-khan-naturalization-ceremony-1919-small.jpg",
        description="Small group of overseas soldiers who applied for Naturalization, June 6, 1919 — same year as Mohaiyuddin Khan",
        tile_url=None,
        item_id="2016827097",
        manual_url="https://www.loc.gov/item/2016827097/",
    ),
    dict(
        slug="1A-khan-naturalization-ceremony-1919-large.jpg",
        description="Large group of overseas soldiers who applied for Naturalization, June 6, 1919",
        tile_url=None,
        item_id="2016827096",
        manual_url="https://www.loc.gov/item/2016827096/",
    ),
]


# ── HELPERS ──────────────────────────────────────────────────────────────────

def fetch_json_api(item_id: str) -> list[str]:
    """
    Hit LC's JSON metadata API for an item and return a list of image URLs
    (highest resolution first).
    """
    url = f"https://www.loc.gov/item/{item_id}/?fo=json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ✗ JSON API failed: {e}")
        return []

    urls = []

    # Path 1: resources[].files[][] contains service/url keys
    for resource in data.get("resources", []):
        for file_group in resource.get("files", []):
            for f in file_group:
                if isinstance(f, dict):
                    u = f.get("url", "")
                    if u and any(u.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".tif", ".tiff")):
                        urls.append(u)

    # Path 2: item.image_url (list of direct URLs)
    item_block = data.get("item", {})
    for u in item_block.get("image_url", []):
        if u not in urls:
            urls.append(u)

    # Path 3: scan entire JSON blob for tile.loc.gov JPEGs
    raw = r.text
    found = re.findall(r'https://tile\.loc\.gov/[^\s"\'<>]+\.(?:jpg|jpeg)', raw, re.IGNORECASE)
    for u in found:
        if u not in urls:
            urls.append(u)

    return urls


def download(url: str, dest: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in r.iter_content(65536):
                fh.write(chunk)
        kb = os.path.getsize(dest) // 1024
        print(f"  ✓ {kb:,} KB  →  {os.path.basename(dest)}")
        return True
    except Exception as e:
        if os.path.exists(dest):
            os.remove(dest)
        print(f"  ✗ Download failed: {e}")
        return False


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    ok, fail = 0, 0
    manual = []

    print(f"Downloading {len(ASSETS)} LC proposal assets → {OUTPUT_DIR}/\n")

    for a in ASSETS:
        slug = a["slug"]
        dest = os.path.join(OUTPUT_DIR, slug)

        # Skip files that already exist and are non-trivially sized (> 50 KB)
        if os.path.exists(dest) and os.path.getsize(dest) > 51200:
            print(f"✓ {slug}  (already exists, {os.path.getsize(dest)//1024:,} KB — skipping)")
            ok += 1
            print()
            continue

        print(f"→ {slug}")
        print(f"  {a['description'][:80]}...")

        image_url = None

        # 1. Direct tile URL
        if a["tile_url"]:
            print(f"  Using direct tile URL")
            image_url = a["tile_url"]

        # 2. JSON API
        elif a["item_id"]:
            print(f"  Fetching JSON metadata for item {a['item_id']}...")
            candidates = fetch_json_api(a["item_id"])
            if candidates:
                # Prefer highest-resolution JPEG (largest size number in URL, or first)
                # tile.loc.gov URLs with "master" are highest quality
                master = [u for u in candidates if "master" in u]
                image_url = master[0] if master else candidates[0]
                print(f"  Found image URL: {image_url[:80]}...")
            else:
                print(f"  ✗ No image URL from JSON API")

        # 3. Attempt download
        if image_url:
            if download(image_url, dest):
                ok += 1
            else:
                fail += 1
                manual.append(a)
        else:
            fail += 1
            manual.append(a)

        time.sleep(0.8)
        print()

    # Summary
    print(f"{'─'*60}")
    print(f"Done. {ok} downloaded, {fail} failed.\n")

    if manual:
        print("Manual download needed for the following — visit the URL,")
        print("click the download icon, and save to proposal-images/:\n")
        for a in manual:
            print(f"  {a['slug']}")
            print(f"  {a['manual_url']}\n")


if __name__ == "__main__":
    main()
