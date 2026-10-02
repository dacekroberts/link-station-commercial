# Final write-up and code audit review

What changed in the project on 2026-09-30 and 2026-10-01, organized by
concept rather than by date. Two sessions did the work: a cleanup session
audited the code on 09-30, and the main session (moving to Opus 5.5 at the
start of this stretch) carried the write-up to the final version on 10-01.
Figures are as of the end of 10-01; `docs/DECISIONS.md` has the dated
entries and the reasoning in full.

## Contents

- [State of the project](#state-of-the-project)
1. [The code audit and its corrected figures](#1-the-code-audit-and-its-corrected-figures)
2. [Comment style and the em-dash rule](#2-comment-style-and-the-em-dash-rule)
3. [Explicit hypotheses](#3-explicit-hypotheses)
4. [Chain prose after the recount](#4-chain-prose-after-the-recount)
5. [The prose review](#5-the-prose-review)
6. [The About page](#6-the-about-page)
7. [Documentation and companion pages](#7-documentation-and-companion-pages)
8. [Working across sessions](#8-working-across-sessions)
9. [How things were verified](#9-how-things-were-verified)
10. [Mistakes and corrections](#10-mistakes-and-corrections)
11. [Open items](#11-open-items)

- [Where things live](#where-things-live)

---

## State of the project

- **Final version, live.** Six pages: Overview & Introduction, Heatmap,
  Findings & EDA, Methodology & Limitations, Flowchart, About.
- **17 commits** across the two days (49 file changes, +2,394 / −1,431
  lines), all pushed. `main` ends at `571dbcc`.
- **Checks pass:** `check_published_numbers.py` (28 citations across four
  files) and `check_no_em_dashes.py`. Every touched page renders without
  errors in a headless run, and each push was confirmed on the deployed
  site.
- **Next:** the presentation, set up in a separate worktree
  (`.claude/worktrees/visuals`, branch `visuals`) with its own handoff.

---

## 1. The code audit and its corrected figures

The cleanup session's line-by-line review of steps 2 to 4 and the Findings
page was the first review of the code itself rather than its output.

| Change | Before | After |
|---|---|---|
| **Chains count distinct locations, not license records** (`00f535a`). One storefront holding two or three licenses had counted as two or three locations. `step4_rings.py` now counts distinct coordinates, rounded to about one meter. | 152 brands, 8.5% of locations | **116 brands, 6.7%** |
| Chain share by ring | 11.0 / 10.1 / 8.3 / 8.5% | **9.5 / 7.5 / 6.8 / 6.8%** (the ring 3 to 4 reversal is gone: 6.82% → 6.77%) |
| Overlap noise (single locations touching more than one station) | 1,589 of 3,900 (40.7%) | 1,604 of 3,900 (41.1%) |
| **Walkshed density** in `station_stats.csv` (`7ec25a3`) is businesses over area, not the mean of three ring densities. Not displayed on the site. | Othello 454 | 230 |
| **Brand normalization** strips legal suffixes only at the end of a name | "FOO L.L.C." and "BLUE CO BAKERY" mishandled | fixed; no chain figure changed |
| **Census cache** (`17c35d7`): a cached batch is reused only if every row's id and address still match | reused by file name alone | refused on mismatch; no current effect |
| **Labels** on Graph 3 and Table 3 | "density" for a business count | "Businesses Within 0.3 Miles", "Business Counts" |

**Added as a limitation, not fixed** (`2033221`): duplicate licenses still
count in the density figures. 113 records share a name and a spot with
another record (91 groups), touching 137 of 6,847 business-ring matches,
about 2%. Fixing it in step 2 would reassign record ids and force a fresh
geocoding run, so it is disclosed on the Methodology page instead.

Unchanged by the audit: every density figure, the 45.5% old-definition
chain figure, and Subway's seven locations across eight stations.

---

## 2. Comment style and the em-dash rule

- **Every code comment and docstring** was rewritten into one neutral
  style (`15134ab`, `1c0811d`): no "I", "we" or "you"; short statements of
  what and why; every measured value kept with its re-measure warning.
  `components.py` is the reference example.
- **`scripts/check_no_em_dashes.py`** (`790239f`) enforces a hard rule of no
  em dashes in any comment or docstring, including CSS and JavaScript
  comments inside Python strings. It scans with Python's tokenizer, its
  syntax tree, and a regex for embedded comments. Visible site text is
  exempt.
- Both rules are written into `CLAUDE.md`.

---

## 3. Explicit hypotheses

**Why.** The Findings page said "my hypothesis" five times but stated it
only twice, and the ridership section never did. A reader was told a
hypothesis was supported without being told what it was.

**How, without rewriting the sections** (`c7a9a91`, `ee335e3`):
- Each analysis section now opens with a bordered **Hypothesis** block and
  closes with a **Result** block (`section_callout()`), each Result opening
  with a one-word verdict: **Supported**, **Loosely supported**, **Both
  supported**.
- **The hypotheses are the pre-data questions.** Writing new ones after
  seeing the results and presenting them as starting points would be
  HARKing. The gradient question is Dace's own wording from the Graph 1
  paragraph; the ridership and chain questions are verbatim from
  `docs/initialscript.md`.
- **The chain question drifted mid-analysis**, so the block states the
  original question, then says it shifted to whether chain share rises
  approaching the platform. The original is answered too: chains appear
  near **2.95** stations on average against **1.66** for single-location
  businesses, a gap partly built in by construction.
- **The Overview gained "What I Asked"**, paired with "What I Found": the
  larger question the project can't settle (does transit bring businesses,
  or follow existing commerce?) and the same three questions word for word.
  The headingless "Businesses cluster near transit" paragraph moved there
  as that question's honest limit, with a new opener pointing back to it.

**Authorship:** the results for the gradient and ridership sections and
the chain bridge are Dace's text with approved fixes; the chain Result,
the Overview caption and the paragraph's opener were drafted at Dace's
request and chosen by Dace.

---

## 4. Chain prose after the recount

The recount left three passages describing a reversal that no longer
existed (`5354b8c`, `721b9a4`).

- **Graph 5 caption, now computed from `chain_ring_stats.csv`:** per square
  mile, chains drop **73.6%** from ring 1 to ring 4 against **61.8%** for
  other businesses, so it can't go stale the way the hand-typed caption did.
- **The ring 3/4 tie, explained as downtown buffer overlap, hedged.**
  Checked against step 4's join with the chain definition held fixed.
  - **For:** Westlake (8.4% → 8.8%) and Symphony (8.2% → 8.2%) show no
    fall-off between rings 3 and 4 and hold 112 of ring 4's 285 chain
    locations (39%). Neighboring downtown platforms sit 0.27, 0.41 and 0.35
    miles apart (measured in EPSG:32610).
  - **Against:** removing SODO and Stadium opens only a 0.38-point decline;
    removing the four downtown stations produces a +1.0-point reversal; and
    Chinatown-ID's ring 3 (3 chains among 121 businesses) pulls ring 3 down
    for an unrelated reason.
  - So the paragraph says "possibly because of" overlap, and the gap
    (0.05 points against roughly ±0.7 of noise) is called a tie.
  - **Rejected:** "ring 4's larger area allows more storefronts". Area
    cancels in a share: ring 4 has 3.0x ring 3's businesses and 3.0x its
    chains.
- **Metric label:** "Brands at more than one station" → "Brands with 2+
  locations". It counts `location_count > 1`; by stations it would be 1,706.
- **In Summary:**
  - Chains lean in "even harder than" other businesses, not "nearly as
    hard". The old sentence read backwards.
  - "Plateauing the chain-share drop-off" replaces "the chain-share
    reversal".
  - "Commercial density", without "that". Every walkshed is the same
    0.282 sq mi, so count and density give the identical r = 0.684.
  - "Advantage" → "opportunity", which is less causal.

---

## 5. The prose review

The cleanup session reviewed the finished Findings page and confirmed every
number independently. Dace triaged its report (`fdc1863`):

- **Accuracy fixes:**
  - 6.7% is a share of chain *locations*, not of all businesses.
  - "Higher earnings potential" → "more businesses nearby" (no earnings
    data).
  - "Still significant" → "still a sizable gap" (no significance test).
  - "Other businesses", not "independent businesses".
  - "Three views of the same data", not three separate measures.
  - The gradient trend "holds in aggregate, though half the stations
    deviate from it individually".
  - Capitol Hill's +38% jump goes "the same direction as" Graph 1's +0.9%,
    not "like" it.
  - "Real" and "not a marginal one" dropped from the opportunity sentence.
- **Consistency and readability:** one ring-step notation ("ring 2 to 3"),
  "moderate" for r throughout, all four downtown overlap stations named,
  "International District/Chinatown", "1 Line", farther/farthest, full
  sentences in the station notes, a simpler Graph 4 sentence, graph-title
  casing.
- **Structure:** the Graph 1 paragraph points to the Hypothesis block
  instead of repeating it; the chain Result no longer repeats Graph 5's
  percentages; the "interactive visuals" note moved under the page title;
  the chain metric tiles and Table 4 follow the prose that explains them.
- **Rejected:** renaming "density" to "count" in eight ridership passages
  (scale invariance makes them identical). Also caught: the review's
  suggested chain Result said chain share "falls toward the platform"; it
  rises, and the shipped sentence says so.

---

## 6. The About page

- **New page** `pages/5_About.py` (`9977875`, `ce7f5c3`): Background,
  Education, What I'm Looking For, Why This Project, Skills This Project
  Demonstrates.
- **Personal material moved off the Overview.** "Why Seattle?" now opens
  with the city's factors and "Starting Assumptions" with the trends. The
  About page is built from Dace's own sentences, reordered and connected;
  the education details, certifications (Noble Desktop Python, 2024; five
  Skilljar courses on Claude Code) and the career text are Dace's.
- **Ripple effects:** the Flowchart's app node lists six pages (re-measured:
  the SVG is still 886.8 px, so the 925 px frame still clears it); the
  README file tree lists the page.
- **AI Use** on the Methodology page now adds that Claude Code helped "edit
  my writing for accuracy and clarity" (`57921d1`). The claim that the
  analysis and every judgment call are Dace's stays, on the standard that
  Dace can explain each drafted sentence in their own words. Commit messages
  record who drafted what.

---

## 7. Documentation and companion pages

- **`docs/DECISIONS.md`:** eight entries for 2026-10-01 (`647d4b0`); the
  cleanup session logged the 09-30 audit itself.
- **`docs/Project Summary.md`** (`571dbcc`): the whole project in 18
  segments, organized by concept.
- **Two companion pages** (artifacts, private until shared):
  - "How Dace Used AI": a plain-language explanation for readers new to the
    technology, with a to-scale ring drawing.
  - "Inside the AI Workflow": the technical version, naming languages,
    functions, constants and the agent's working loop.
- **Visuals setup:** the `visuals` worktree with a handoff (storyline,
  verified figures, the exact palette from the code, capture list,
  constraints) and a kickoff prompt.
- **AI memory:** the presentation plan now points at the worktree; the
  About page's résumé link and photo are recorded as an open decision.

---

## 8. Working across sessions

- **Two sessions, one working tree.** The cleanup session and the main
  session edited the same files at times. The main session declared its
  uncommitted preview edits; the cleanup session staged around them, and
  the main session held edits until the cleanup session confirmed its
  chain numbers were final. Committing only the finished part of a
  half-finished file used a staged blob (`git hash-object` and
  `git update-index`), verified on an exported copy of the index.
- **Session identity by folder.** Two sessions were both named "Cleanup",
  one belonging to the sister project; messages went only after confirming
  the working directory. Session references also changed after an
  overnight restart.
- **The sister project's broadcasts** (heavy-job notices, build rules, a
  Paris tram decision) reached this session through a shared session name.
  They were not acted on, and a standing rule now says to ignore them. One
  notice blamed an orphaned 4.7 GB `grep`; it was traced to the other
  project and left alone.
- **Push gating.** The cleanup session held its four commits until the
  reversal passages were reworded; the main session pushed them with its
  own once Dace said so.

---

## 9. How things were verified

- **Independent replication:** the chain recount was reproduced from step
  4's own functions (116 brands; 9.52 / 7.49 / 6.82 / 6.77%), and the
  caption's 73.6% / 61.8% was recomputed separately before it shipped.
- **Station spacing** measured in EPSG:32610 (meters), per the project's
  distance rule.
- **The numbers check** after every figure change, with each new hand-typed
  figure registered; figures it can't derive (the station spacing, the
  Westlake/Symphony shares) are listed as not checked.
- **Headless renders** of every touched page with Streamlit's `AppTest`
  before each commit, including the staged version on its own.
- **Live-site checks** after each push: label, caption, tie wording,
  verdicts, About page content and section order.
- **The flowchart frame** re-measured from inside the iframe with a
  temporary `postMessage` probe, since its contents can't be read from the
  page.
- **Every summary and companion page** fact-checked against the code and
  the decision log before publishing.

---

## 10. Mistakes and corrections

| What | Caught by | Correction |
|---|---|---|
| A commit message called the Graph 5 paragraph "the user's text" when most of it was drafted at Dace's request | Review before pushing | Amended the unpushed commit to record authorship accurately |
| A registered citation phrase split across two concatenated string literals, twice | The numbers check failed before commit | Re-wrapped; the limit is now documented in the script |
| A `\n\n` escape became real line breaks through a shell heredoc | The file failed to parse | Rebuilt with `chr(92)`; later scripts written with the file tool instead of the shell |
| A worksheet note said the ridership comparison should note "count, not density" | Checking scale invariance | Withdrawn: count and density give identical results |
| The Project Summary's first draft stated three details from memory (the mojibake cause, tooltip contents, the 311 cause) | Checking against the decision log | Corrected before showing it |
| The plain-language page said "over the months" and overstated the cleanup session's role and the version re-checks | Fact-check before publishing | Corrected before publishing |
| The technical page first named `MarkerCluster` | Checking names against the code | `FastMarkerCluster`; two function descriptions also sharpened |
| The cleanup review's suggested chain Result said chain share "falls toward the platform" | Checking direction against the data | The shipped sentence says it rises |

---

## 11. Open items

- **Résumé link and photo** on the About page: Dace is still deciding.
- **The presentation:** ready to start in the `visuals` worktree. The
  ridership figures need a decision before they appear in a deck or video
  (Sound Transit's terms).
- **Duplicate licenses** in the density figures (about 2%): a documented
  limitation, deferred.
- **`.backups/pre-rewrite-backup.bundle`:** the local backup from before the
  history rewrites, deletable when no longer wanted.
- **The `visuals` branch** exists only locally.

---

## Where things live

| What | Where |
|---|---|
| Hypothesis blocks, chain prose, In Summary | `pages/2_Findings_&_EDA.py` |
| "What I Asked", moved paragraph, Why Seattle, Starting Assumptions | `Overview_&_Introduction.py` |
| About page | `pages/5_About.py` |
| AI Use clause, duplicate-license limitation | `pages/3_Methodology_&_Limitations.py` |
| Six-page flowchart node | `pages/4_Flowchart.py` |
| Chain recount, walkshed density | `src/step4_rings.py` |
| Census cache check | `src/step3_geocode.py` |
| Citation registry and not-checked list | `scripts/check_published_numbers.py` |
| Em-dash rule | `scripts/check_no_em_dashes.py`, `CLAUDE.md` |
| Dated reasoning | `docs/DECISIONS.md` (2026-09-30 and 2026-10-01 sections) |
| The whole project, by concept | `docs/Project Summary.md` |
| Visuals handoff and kickoff prompt | `.claude/worktrees/visuals/.claude/handoffs/` (local) |
