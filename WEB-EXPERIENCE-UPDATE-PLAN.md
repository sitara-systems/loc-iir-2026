# Web Experience Update Plan

**Purpose:** Align the two web prototypes with the sharpened thesis — from "what did the archive know?" to "what did they know and choose not to tell us?"

**Status:** Both prototypes already lean toward the accountability narrative. The scrollytelling piece (`what-did-they-know.html`) uses the three-act structure (archive knew first / government catches up / the silence) and the search experience (`search-the-silence.html`) demonstrates the silence interactively. The updates below deepen the thesis rather than restructure.

---

## 1. Add Personal Prologue to Both Experiences

**What:** A brief "what I expected to find" section before the narrative begins — the viewer's entry point mirrors Nathan's own research journey.

**Where:** New section between the hero and Chapter I in `what-did-they-know.html`; new preamble before the first search in `search-the-silence.html`.

**Content (draft):**

> I started this project looking for glaciers. I imagined photographs from USGS surveys — Montana in 1880, in 1920, in 1960 — a landscape declining so slowly that no one alive at any single moment would have noticed. I thought the story was about evidence hiding in plain sight.
>
> That is not the story the archive tells.

**Why this matters:** It sets up the emotional reversal. The viewer arrives expecting a detective story about slow change and gets hit with an accountability narrative about institutional silence. That's the moment that makes the project land.

**Implementation:** ~15 lines of HTML. New `.prologue` section with the same visual language as the existing interstitials.

---

## 2. Sharpen the Chapter II Transition

**What:** The transition from "The Archive Knew First" to "The Government Catches Up" currently reads as chronological progression. It should feel like a shift in genre — from discovery to confrontation.

**Where:** The `ch-head` for Chapter II in `what-did-they-know.html`.

**Current:** "The Government Catches Up — In 1965, the White House finally reads what the archive already held."

**Proposed:** "The Government Is Told — In 1965, the White House receives a formal warning. Watch what happens to the public record."

**Why:** "Catches up" is passive — it suggests the government was behind but well-intentioned. "Is told" is active — it frames what follows as a choice, not a delay.

---

## 3. Strengthen the Silence Section

**What:** Add the contrast numbers from `search-the-silence.html` to the silence section in `what-did-they-know.html`, and add a brief note about what the *institutional* record was doing during the same period.

**Where:** The `.silence` section in `what-did-they-know.html`.

**Add:** A second row to the silence grid showing institutional activity during 1966–1987:

| Public Record | Institutional Record |
|---|---|
| 1 page mentioning CO₂ + climate, 1960–75 | 1970: Clean Air Act (addresses smog, ignores CO₂) |
| 1 page mentioning "global warming" before 1988 | 1979: Charney Report confirms 1.5–4.5°C sensitivity |
| 4 pages mentioning "greenhouse effect," 1960–87 | 1983: EPA warns of "catastrophic" warming by 2100 |

**Why:** The silence is most devastating when shown against the institutional activity happening at the same time. The newspapers went quiet; Congress kept commissioning studies. Both records are at LC.

---

## 4. Add "What Changed?" Epilogue

**What:** A brief section after Hansen/1988 that names what the silence cost — not in terms of climate outcomes, but in terms of public understanding and democratic participation.

**Where:** After the convergence section, before the closer, in `what-did-they-know.html`. After the finale in `search-the-silence.html`.

**Content (draft):**

> For twenty-two years, the government studied a problem the public didn't know existed. When Hansen broke the silence in 1988, Americans had no framework for what they were hearing. No memory of Foote, Arrhenius, Callendar, or Revelle. No sense that the evidence had been in their newspapers for a century before it was in their government's reports.
>
> The silence didn't just delay action. It made the public conversation start from zero — as if the science were new, as if the concern were recent, as if we were the first generation to understand.
>
> We were not. The archive proves it.

**Why:** This closes the loop on the thesis. The silence isn't just an interesting archival finding — it has consequences that persist today. Most Americans still believe climate concern began in the 1980s.

---

## 5. Fix Image Paths for New Repo Structure

**Status: DONE.** Both HTML files updated from `../lc-archive-search/climate-images/` to `../../research/climate-images/`.

**Note for GitHub Pages:** When deployed, the `web/` directory becomes the root. Image paths currently point outside `web/` to `research/`. For production deployment, either:
- (a) Copy the needed climate images into `web/what-did-they-know/images/` and update paths, or
- (b) Add a build step that copies `research/climate-images/` into the `web/` deploy artifact

Option (a) is simpler and recommended for the prototype stage.

---

## 6. Cross-Link the Two Experiences

**What:** Add navigation between the scrollytelling narrative and the interactive search. Currently they're standalone pages with no way to get from one to the other.

**Where:** Add a link in the closer section of each page pointing to the other.

**From `what-did-they-know.html`:** "Search the archive yourself →" linking to `search-the-silence.html`

**From `search-the-silence.html`:** "Read the full narrative →" linking to `what-did-they-know.html`

---

## Priority Order

1. **Fix image paths for GitHub Pages deployment** (move images into web/) — required for anything to render
2. **Add personal prologue** — highest narrative impact, small code change
3. **Sharpen Chapter II transition** — one line change, significant tonal shift
4. **Cross-link the two experiences** — simple, necessary for reviewers
5. **Strengthen the silence section** — moderate effort, strong editorial payoff
6. **Add epilogue** — moderate effort, closes the thesis

Items 1–4 are an afternoon of work. Items 5–6 are a second pass.
