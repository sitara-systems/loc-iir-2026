# LC IIR Project

Web experiences and research tools for the Library of Congress Innovator in Residence program (BAA 030ADV26R0021).

## Project Structure

```
web/                          # Static web experiences (deployed via GitHub Pages)
├── what-did-they-know/       # Climate science record exploration
│   ├── what-did-they-know.html
│   └── search-the-silence.html
└── hidden-in-plain-sight/    # Immigration & identity narrative
    ├── hidden-in-plain-sight.html
    └── images/

scripts/                      # LC API search & image download tools
├── lc_search.py              # General LC collection search
├── lc_climate_search.py      # Climate-focused newspaper search
├── download_images.py        # Proposal image downloader
├── download_climate_images.py # Climate image downloader
├── lc_search_hips.py         # Hidden in Plain Sight search variant
└── requirements.txt

research/                     # Search results, findings, and downloaded images
├── climate-images/
├── proposal-images/
└── *.md / *.json             # Search results and analysis
```

## Web Experiences

Two interactive prototypes exploring LC digital collections:

- **What Did We Know?** — Traces over 150 years of climate evidence through LC's newspaper archives, scientific journals, and government documents
- **Hidden in Plain Sight** — Two family histories (Nino-Dominguez, Khan/Mohaiyuddin) documented in LC collections but obscured by current discovery tools

## Scripts

Search tools that query the LC's public APIs (loc.gov API + Chronicling America). No API key required.

```bash
pip install -r scripts/requirements.txt
python scripts/lc_search.py
python scripts/lc_climate_search.py
```

## Deployment

The `web/` directory is automatically deployed to GitHub Pages on push to `main`. Enable GitHub Pages in your repo settings under **Settings > Pages > Source: GitHub Actions**.

Once enabled, web experiences will be available at:
- `https://<username>.github.io/lc-iir-project/what-did-they-know/`
- `https://<username>.github.io/lc-iir-project/hidden-in-plain-sight/`
