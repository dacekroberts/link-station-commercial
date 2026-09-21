# Verification and data integrity review

Covers the second half of 2026-09-20: an independent verification pass over
the whole project, the fixes that came out of it, and a privacy check on what
the map publishes. Organized by concept rather than by date. **This is a map,
not the record of truth:** `DECISIONS.md` is authoritative for exact reasoning
and values, and `git log` for exact changes. The visual-polish work earlier
the same day is in `Visual Design & Heatmap Review.md`.

## Contents

1. [State of the project](#state-of-the-project)
2. [The production risk that was closest to biting](#1-the-production-risk-that-was-closest-to-biting)
3. [Data integrity: what was verified and what was wrong](#2-data-integrity-what-was-verified-and-what-was-wrong)
4. [Publishing people's names](#3-publishing-peoples-names)
5. [Licenses and terms of use](#4-licenses-and-terms-of-use)
6. [Repository hygiene](#5-repository-hygiene)
7. [Map and interface changes](#6-map-and-interface-changes)
8. [How things were verified](#7-how-things-were-verified)
9. [Mistakes and corrections](#8-mistakes-and-corrections)
10. [Open items](#9-open-items)
11. [Where things live](#where-things-live)

## State of the project

- **Live and verified.** All five pages serve correctly from Streamlit Cloud,
  checked directly rather than assumed.
- **Numbers audited.** Every hardcoded figure on every page was checked
  against `outputs/`, `config.py`, or a fresh recomputation. Three were stale;
  all three are fixed.
- **Pipeline reproduces exactly.** A full from-scratch re-run produced five
  byte-identical CSVs and a `heatmap.html` identical after normalizing
  Folium's random element ids.
- **No deprecated Streamlit APIs remain.** The app went from 14 deprecation
  warnings per page load to zero.
- **Dependencies bounded.** `requirements.txt` now carries upper bounds,
  tested against what the deploy actually resolves.
- **No personal names published.** Seven sole proprietors were being mapped
  by name at their home addresses; the map now withholds them.
- **Every data source's terms read and logged** for the first time, in
  `data_sources.md`. One conflict found, and a permission request sent.

Commits are listed against each section below rather than here, since four
history rewrites in one day renumbered them repeatedly. If a hash does not
resolve, find the commit by its subject line — see the note in
`Visual Design & Heatmap Review.md`.

---

## 1. The production risk that was closest to biting

**Two Streamlit APIs were past their announced removal dates while the site
was live**, and `requirements.txt` pinned `streamlit>=1.40` with no upper
bound. Streamlit Cloud re-resolves that file on every rebuild, so the next
push after an actual removal would have taken pages down with no code change.

| API | Removal announced | Where |
|---|---|---|
| `st.components.v1.html` | 2026-06-01 | Heatmap and Flowchart embeds |
| `use_container_width` | 2025-12-31 | 10 call sites on the Findings page |

**The heatmap** moved to `st.iframe(HEATMAP_HTML)`, which takes the `Path`
directly and reads it as UTF-8. That retired the explicit `encoding=` that
Windows needed to stop it mangling the em dashes in layer names — verified by
confirming `Retail — NAICS Code: 44/45` still renders on the live site.

**The flowchart** could not use the same call, because it builds its HTML in
Python rather than reading a file. `st.html` takes a string directly and
looked like the obvious answer; it was tested and **rejected**, because it
renders *inline rather than in an iframe*. A probe confirmed the document's
own `html, body { background }` rule bleeding onto an unrelated element in
the page. It goes through `st.iframe` as a base64 `data:` URL instead, which
stays sandboxed and still loads Mermaid from its CDN.

**Bounds added:** `streamlit>=1.40,<2`, `pandas>=2.2,<4`, `altair>=5,<7`,
verified against the versions the deploy actually resolves (pandas 3.0.6,
Streamlit 1.64.0, altair 6.3.0) rather than guessed.

---

## 2. Data integrity: what was verified and what was wrong

### Wrong, and fixed

| Figure | Was | Is | Where |
|---|---|---|---|
| Chain correction | 45.7% | **45.5%** | Flowchart diagram |
| Page count | "4 pages" | **"5 pages"** | Flowchart diagram |
| Businesses in any ring | 4,116 | *removed* | Methodology |

The first two were pre-existing staleness. The `45.7%` predated the corporate
food-service contractor exclusion; the "4 pages" node told the reader the site
had four pages while they stood on the fifth.

**The 4,116 was subtler and worth understanding.** It was correct for its own
computation — unique businesses in step 4's polygon spatial join — but the
Overview shows **4,120**, from step 5's distance-based count. The gap is four
businesses sitting 965.399 m from their nearest station: 20.7 cm inside the
true 0.6-mile circle, but outside the 64-sided polygon `shapely.buffer()`
actually draws. `DECISIONS.md` already reconciled 6,847 against 4,120 as a
deliberate choice, but never mentioned this third number. The sentence was
rewritten to drop the total; the `1,767 (42.9%)` it exists to report is
unchanged.

### Verified correct

Everything else. The audit covered 40+ figures:

- **Headline numbers:** ring densities 957/550/592/311, the 67.5% fall,
  r = 0.684, the 1.8× variance ratio (1.757), 152 chain brands at 8.5%,
  4,120 of 11,409.
- **Station-level claims:** three separate "zero businesses in this ring"
  assertions (Northgate ring 1, University of Washington ring 1, Rainier
  Beach ring 3), and the 17 and 5 business counts.
- **Claims needing a rebuilt spatial join,** because `chain_ring_stats.csv`
  cannot isolate individual stations: Stadium's ring 4 carrying 31 chain
  matches of 373, SODO's 18 of 149, and that removing those two stations
  turns the aggregate ring-3-to-4 move from a rise into a decline
  (8.7% → 8.4%). All three reproduce exactly.
- **All 21 heatmap layer counts.**

Two statistical claims looked false at first and are not:

- **"957 to 311"** — the true values are 956.5 and 310.5. Python's banker's
  rounding gives 956/310; conventional rounding gives 957/311, which is what
  the site uses.
- **"Each of the top three stations sits at least 0.5 standard deviations
  above the one below"** reads false against business density, where
  Westlake→Symphony is 0.42 sd and two stations are exactly tied. The sentence
  is about *ridership*, where the gaps are 0.93, 0.75 and 0.57 sd. The fourth
  drops to 0.13 sd, which is why the claim stops at three.

### Not machine-checkable

Two figures are honestly framed as one-time checks but cannot be re-derived
from committed data, so no future audit can confirm them either:

- The **48 m mean platform offset** (a Session 2 hand measurement).
- **r = 0.998** between the two ridership metrics. The second metric was
  deliberately never transcribed — that was the finding — so the correlation
  cannot be recomputed.

---

## 3. Publishing people's names

The map plots every in-ring business by name at a geocoded address, and the
registry behind it lists home-based sole proprietors alongside storefronts.
A trade name someone chose is commercial information; a registrant's own name
at their house is not, even though the registry holding it is public.

Prompted by a portable write-up passed over from the sibling multi-city
project, where the same question found a real problem.

**Three of its four recommendations were already in place here** — `812990`
and `812930` excluded, `459999` kept. The fourth does not apply: its largest
finding was NAICS `454` (nonstore retailers) being swept in by a broad `45`
prefix, which this project's prefix list also matches, but Seattle has only 29
such rows and **all sit beyond the outer ring, so zero reach the map.**

### The signal that worked, and two that did not

1. **The owner-name fallback** in step 2 fires on 22 of 84,390 raw rows, and
   **none reach the map.** Measured against the raw export, never the
   processed file — step 2 renames the trade column and fills its blanks in
   one pass, so the processed file reads as zero blanks either way.
2. **A "looks like a person" regex** fires on 42.4% of all pins. That is a
   false-positive floor, not exposure.
3. **Intersecting it with zoning** narrows to 230 pins (5.58%) on
   residentially zoned land, which reads alarming until the rates are
   compared: 48.3% of pins in residential zones are person-like against 41.9%
   in commercial ones — **+6.4 points**. Almost all of that 5.58% is the floor
   redistributed.
4. **What actually answered it:** the registry carries *both* a trade name and
   a legal entity name. Someone who chose a trade name has two different
   strings; someone who never chose one is published under whatever the
   registry holds. Requiring **published name == legal entity name AND a sole
   proprietorship** identifies that case directly.

The sole-proprietorship condition is load-bearing. Without it, single-member
LLCs swamp the result, because an LLC's legal name *is* its brand ("Barking
Gorgeous LLC", "Blue Sky Bridal"). It deliberately does not flag someone who
filed an LLC under their own name, which is a commercial identity they chose.

**Result: 4,120 pins → 41 → 12 on residential land.** Small enough to read in
full rather than sample. Seven are genuinely someone's name; five are trade
names that happen to match the legal one ("Boy Scout Troop 151", "Hami
Salon", "Tigi's Fragrance Corner"). **About 7 of 4,120 — 0.17%** — three of
them on single-family land.

### The seven names are withheld from the map

Measuring the exposure was not the same as acting on it, and for a while it
stood in for acting on it: the number was small, so the names stayed up. That
conflated two different questions. "0.17% is negligible" is a judgment about
proportion; whether it is appropriate to publish seven identifiable people at
their homes is not a question proportion answers.

`step5_map.py` now substitutes `Name withheld (sole proprietor)` wherever a
pin's name is the registrant's own identity by the test above. Three things
made this cheap:

- **It needs no zoning.** The test reads only `business_name`,
  `Business Legal Name` and `Ownership Type`, all already in
  `businesses_geocoded.csv`. Zoning was only ever needed to *size* the
  problem, not to identify the rows, so the filter adds no data source and no
  dependency.
- **It changes a label, not a row.** The pin, its coordinates, its category
  and its ring all stay, so every figure on the site is untouched — the
  regenerated map still carries 4,120 pins and the same 1,703 / 1,786 / 631
  group counts.
- **It recomputes itself.** A hand-written list of the seven would go stale
  against a newer license export with no warning; this rule re-derives from
  the registry on every run.

It covers **41 pins**, not seven, because it deliberately over-reaches: about
three dozen are trade names that happen to equal the legal name ("Hami
Salon", "Boy Scout Troop 151") and lose their label too. That is the accepted
price of a rule that cannot rot.

**Substituted where the pin arrays are built, not in the tooltip's
JavaScript.** The pin data is baked into `heatmap.html` as a literal array, so
hiding a name at render time would have left all seven readable in the page
source. Verified at coordinate level: 8,240 pin entries (4,120 × 2 layers, so
nothing dropped), all 41 carrying the substitution at their own coordinates,
and zero real names surviving in any escaping — checked against JSON-escaped
forms too, since two of the 41 contain apostrophes.

One case worth keeping: a search for surviving names returns `JULIUS`, which
is **not** a leak. Two businesses trade under that name — one whose legal name
is `JUJU SOLO PROJECT`, a chosen trade name that is correctly still shown, and
one whose legal name is also `JULIUS`, correctly withheld. Only the
coordinate-level check could tell them apart; a name search alone would have
reported a false leak.

**Zoning stays out of the pipeline.** Wiring it in would add a fourth manual
data source, a failure mode when the city republishes the layer, a full
re-run, and a Methodology paragraph disclosing it as an input — and the
withholding rule above does not need it. The layer
(`data/raw/seattle_zoning.geojson`, 3,627 polygons, matched 100% of pins) is
gitignored and the script degrades to the name signals without it. Both paths
are tested. The fetch URL lives in the script's docstring, not in
`data/raw/README.md`, because that file lists what the *pipeline* requires.

A new Limitations subsection on the Methodology page discloses all of this in
the site's own voice.

---

---

## 4. Licenses and terms of use

No source's license had ever been read. The Citations section cited two
academic papers and no datasets; the only attribution anywhere was the
OpenStreetMap credit Folium emits automatically, which nobody had chosen.

This matters more here than for a project that only displays data, because
this repository **redistributes derived data publicly** — `heatmap.html`
carries 4,120 business records with coordinates, and the station geometry is
republished as map data. Full log in `data_sources.md`; the short version:

**The first pass looked in the wrong place.** Dataset-level metadata answered
three sources and left three open. Two of those three were settled by
**portal- and site-level** terms, which is where I should have looked next
rather than concluding they could only be resolved by asking.

| Source | Outcome |
|---|---|
| Seattle business licenses | Public Domain, explicit |
| Seattle GIS donor layer | no dataset grant, but covered by the portal terms |
| Seattle zoning | PDDL |
| Sound Transit GTFS | revocable, with a **flow-down** clause — now discharged |
| Sound Transit ridership | **conflict**, see below |
| US Census geocoder | notice required, now displayed |
| OpenStreetMap | ODbL + tile policy, compliant |

**Two obligations were unmet and are now met.** Sound Transit's GTFS terms
require passing them to anyone who receives the data — this project
republishes GTFS-derived geometry and passed nothing on. The Methodology
page's new "Attribution and terms" note does that. Separately, the Census
API terms prescribe a notice, now displayed verbatim.

**One condition worth remembering.** Seattle's portal bars commercial use of
data that "can be readily sorted, filtered, or configured as a list of
individuals." This data demonstrably can — `check_personal_exposure.py` does
exactly that. A portfolio is not a commercial purpose, so the project is
within it; monetizing would change that.

**One genuine conflict, unresolved.** Ridership was transcribed from a page
on `soundtransit.org`, so its **website** terms govern, not the Open Transit
Data terms. They license content "as an informative resource" and prohibit
"reproduction... distribution... republication" without prior written
permission, with no carve-out for data or statistics. This project
republishes those figures in `station_stats.csv`, Graph 3, Graph 4 and
Table 2, and derives r = 0.684 and the 1.8x comparison from them.

Recorded as a gap between what the page says and what the repo does, **not
as a legal conclusion** — facts are generally not copyrightable while site
terms operate as contract, and that is not a question this project resolves.
A permission request went to Sound Transit on 2026-09-20; their terms invite
one, and designate the Marketing Division by post as the formal route.

**OpenStreetMap passes, including the part our own code could have broken.**
ODbL requires visible attribution: the control renders at 197x14px in both
modes, 12.6:1 contrast light and 6.6:1 dark. The tile usage policy forbids
pre-emptive fetching: a page load requests 15 tiles, the visible viewport.
The risk the dark mode introduced was double-fetching, since it adds a second
tile layer — measured, and toggling produces **0 new network requests**, all
15 served from cache. The real exposure is availability rather than
compliance: the policy offers no SLA, so an outage breaks the basemap.

## 5. Repository hygiene

### The email, purged from history

`Initial Build Development Context.md` carried the project owner's personal
email in plaintext in a public repo — defeating the point of the repo-local
GitHub noreply identity chosen precisely so no personal email would sit in
history. It was in **two** commits, not one.

Rewritten across all 190 commits with `git filter-repo --replace-text`, then
force-pushed. Verified by diffing the old remote tip against its rewritten
twin: exactly one line changed, commit count and both author identities
intact.

### Internal build notes, removed entirely

A session-by-session build log is working material, not part of a portfolio
deliverable aimed at hiring managers. Delisted first, then purged outright.

**The rename nearly defeated it.** The file had previously been
`Sessions 1-7 Context.md`, so purging only the current path left the same
content in three older commits under the old name. Both paths were purged.
Copies of both live in `.backups/`, one reconstructed from history before it
was destroyed.

### Documentation moved to `docs/`

`DECISIONS.md`, `PLAN.md`, `initialscript.md`, `Development Process
Insights.md` and `Visual Design & Heatmap Review.md`. `README.md` and
`CLAUDE.md` stay in the root — GitHub renders the first, Claude Code reads
the second.

Moved with `git mv` so each keeps its history as a rename. 21 prose references
were repointed in code comments and root files, plus 28 in the local-only
`.claude/` skills.

**The dated entries in `DECISIONS.md` and the checked-off items in `PLAN.md`
were deliberately not rewritten**, per the `safe-rename` skill's rule that
they record what was true when written. That cost nothing: references between
the moved files are bare filenames and they moved together, so they still
resolve. Only references from files that stayed behind needed prefixing.

### Commit hashes are rewrite-sensitive

Four history rewrites in one day broke the hashes cited in the visual review
twice. `filter-repo`'s `commit-map` only retains its most recent run, so it
cannot chain across several; the reliable recovery is by commit subject. A
rewrite only renumbers commits from its earliest change onward, which is why
the third purge left those particular hashes untouched.

---

## 6. Map and interface changes

**Food service pins recoloured orange → magenta `#C2185B`.** Turning the heat
layer orange earlier the same day left the pins 6 degrees of hue from the heat
ramp, so they sank into the densest areas — exactly where food service is most
worth reading. Magenta sits 47 degrees off the ramp while staying 123 from the
retail blue and 177 from the personal-services aqua, and lifts white numeral
contrast from 3.2 to 5.9. Plum and violet were rendered side by side on the
same downtown view before choosing; violet was ruled out on measurement (43
degrees from the retail blue, and the two read alike at cluster size).

**The map follows the visitor's system theme.** It opens on
`prefers-color-scheme` rather than always light, and follows later OS changes
until the visitor works the switch themselves, after which their choice wins.
Nothing is stored, so a reload resumes following the system.

**A site-wide light/dark toggle was confirmed possible and decided against.**
Adding `[theme.light]` and `[theme.dark]` blocks *does* bring Streamlit's
System/Light/Dark control back, so the earlier "an explicit theme removes the
toggle permanently" is only true of a single `[theme]` block. Light mode
breaks three colors hardcoded outside the theme — the sidebar "Pages" label
renders at **1.01:1** contrast (invisible), the Flowchart's Mermaid iframe
stays a dark box on a white page, and the social icons fall to **2.77:1** —
and the ring ramp would need retuning on top. Two of those are one-line
fixes; the ring ramp is not, and that is what settles it. Full reasoning in
section 9, recorded as a decision rather than a pending task.

---

## 7. How things were verified

- **The architecture invariant was proven, not assumed.** `data/` was deleted
  entirely and all five pages loaded in a venv installed from
  `requirements.txt` alone. Zero errors. This rules out a repeat of the
  Session 9 production `FileNotFoundError`, which a local server would have
  masked.
- **The lean venv reproduces the deploy**, not the dev machine — the full
  `.venv` can pass while depending on a package Streamlit Cloud never
  installs.
- **The pipeline was re-run from scratch** and diffed, with Folium's random
  element ids normalized first.
- **Measurement beats eyeballing**, but has its own traps. Three readings
  during this session were artifacts, not findings:
  - The switch thumb read as an identity transform because the browser pane
    was hidden, freezing CSS transitions at frame 0.
  - Graph 2's canvas read as 614px inside a 1000px full-screen box because
    the measurement landed mid-transition.
  - The live system-theme listener could not be tested at all: the browser's
    media emulation updates `matchMedia().matches` without dispatching a
    `change` event inside an iframe. A freshly attached, known-good probe
    listener also saw zero events, which is how it was identified as an
    emulation limit rather than a bug.

  The habit that caught all three: when a measurement contradicts
  expectations, check the measurement before believing the result.

---

## 8. Mistakes and corrections

1. **A file was published before anyone read it.** A skill write-up passed
   over from the sibling project was swept into a commit by a blanket
   `git add -A` and pushed, before being opened. Caught ~20 minutes later
   while auditing the root directory, then purged from history. The content
   was harmless, but nothing about the sweep depended on that. **The practice
   that caused it — staging with `git add -A` rather than naming paths — is
   the thing worth not repeating**, particularly in a repo spending the same
   day having unreviewed material removed from it.
2. **The initial verification report said the email was in one commit.** It
   was in two; the earlier one surfaced only when the purge was run.
3. **The build-notes purge initially missed the file's former name**, leaving
   the same content in history under `Sessions 1-7 Context.md`.
4. **A bug was written into the privacy script and caught by testing it**:
   with no zoning layer and a clean fallback, both result frames are empty and
   `pd.concat([])` raises — the exact path a fresh clone hits.
5. **The first residential-address signal repeated the trap its own source
   document warned about**, lumping `STE` in with `APT`. Seattle encodes units
   as a bare `#`, so 32.2% of addresses were unclassifiable and the first
   "0.10% confirmed" was a measurement gap, not a clean bill of health.
6. **A draft of a `DECISIONS.md` entry quoted the purged email verbatim**,
   which would have reintroduced it to the public repo. Caught before writing.
7. **The license probe stopped at the wrong level.** Dataset metadata
   answered three sources; I reported the other three as unresolvable by
   reading and needing to be asked. Two were answered by portal- and
   site-level terms, which is the obvious next place to look. Checking
   `data.seattle.gov`'s own Terms of Use resolved the GIS layer outright and
   surfaced a non-commercial condition nothing else had mentioned.
8. **The permission contact in the first draft email was wrong.**
   `main@soundtransit.org` is listed in the terms for intellectual-property
   complaints, unsubscribing and general feedback — not for reuse requests,
   which are directed by post to the Marketing Division. Caught by checking
   the address before the email was sent rather than after.

---

## 9. Open items

**Waiting on someone else**
- **Sound Transit's answer on the ridership figures** (section 4). A
  permission request went out 2026-09-20. It is the only open item that could
  change what the site publishes: a "no" would touch Graph 3, Graph 4,
  Table 2 and one of the three analyses. A reminder is scheduled for
  2026-09-27, with the postal route to the Marketing Division as the
  escalation if there is no reply.

**Checked outside the tooling, 2026-09-20**

Both of these needed a real device or a real browser, and both passed. They
are recorded because neither could have been settled from here, and because
one of them is the only confirmation that a piece of shipped behaviour
actually works.

- **Graph 2 on a phone**, confirmed rendering correctly. Previously only
  measured at an emulated 375px viewport, which is not the same thing: the
  original bug was a fixed 900px chart overflowing its container with
  nothing to scroll it, and only Ring 1 visible.
- **The map following a real OS theme switch.** Windows was flipped between
  light and dark with the live site open in an ordinary browser; the map
  followed without a reload and the sun/moon switch slid with it. This was
  untestable from here — the browser's media emulation updates
  `matchMedia().matches` without dispatching a `change` event inside an
  iframe, and a known-good probe listener saw none either. Until this, the
  mid-session listener was shipped but unverified.

**Resolved: the storefront percentages behind the NAICS calls**

The `812990` exclusion rests on a 40-row hand sample finding ~90%
non-storefront, and the `459999` keep on a 25-row sample finding ~70%
plausible storefronts. A seeded 195-row sample was drawn to re-test both at
3x, then retired unread: the sibling project's write-up corroborates both
calls from a **different city's data**, which is stronger evidence than a
larger sample of the same Seattle rows would have been. It reports that
excluding `812990` there cut fallback-traceable personal names from 3,998 to
1,803 — exactly the effect "~90% home-based sole proprietors" predicts — and
endorses keeping `459999`. Seattle's own numbers point the same way: after
the exclusion, this map publishes 0 fallback-traceable names and 7
owner-identity names in 4,120 pins.

Worth being clear about what that does and does not settle. It corroborates
the *character* of the two categories across two independent registries. It
does not re-measure the Seattle percentages themselves, so the figures on the
Methodology page remain the original hand-sample numbers, correctly described
there as hand samples of 40 and 25 rows. The seeded sample is reproducible
from `scripts/`-adjacent code in `DECISIONS.md` if anyone wants to revisit it.

**Decided against, with reasons**

These are settled, not pending. Recorded with their reasoning so a later
reader can disagree on the merits rather than assume they were overlooked.

- **A visitor-facing light/dark toggle for the whole site.** Confirmed
  technically possible — `[theme.light]`/`[theme.dark]` blocks do restore
  Streamlit's control. Not doing it, for four reasons:
  1. **The thing most likely to matter already works.** The heatmap, the
     project's visual anchor and the only page a visitor lingers on, already
     follows the system theme and carries its own switch.
  2. **The ring ramp is not a one-time retune.** That palette encodes
     meaning — bold ring 1 to pale ring 4 maps to near-to-far. On white,
     pale ring 4 vanishes, so it would need either two ramps that read
     differently from one another or one compromise ramp that is worse on
     both. Ring 4 alone took four iterations to settle on dark. This is a
     design regression risk, not a CSS chore.
  3. **The flowchart is dark by design.** Its Mermaid theme uses warm
     charcoal variables chosen deliberately over Mermaid's cool built-in
     dark; theme-awareness means maintaining two variable sets.
  4. **It converts a finished decision into permanent overhead.** Every
     future color choice would need checking against two backgrounds.

  The other two blockers are trivial by comparison: the sidebar "Pages"
  label at 1.01:1 and the social icons at 2.77:1 are one-line fixes.

  *What would change this:* accessibility feedback that the dark theme is
  hard to read, the site acquiring daily users, or the ring ramp being
  redesigned for other reasons anyway.

  *Worth knowing:* light mode was never implemented here. Before the theme
  file existed, visitors had Streamlit's built-in toggle with stock colors;
  setting a theme removed it as an unnoticed side effect, which this
  session's audit is what caught.
- **Zoning as a pipeline input.** The withholding rule needs only registry
  columns already present, so zoning sized the problem and is not needed to
  solve it (see section 3).
- **A keyed or self-hosted tile provider.** Current usage is ordinary and
  compliant; the reason to revisit would be traffic or an OSM outage, not
  licensing (see section 4).

**Conditional, worth not forgetting**
- Seattle's portal bars commercial use of data that can be configured as a
  list of individuals, which this data can. Monetizing the project would
  engage that condition (see section 4).

**Documentation**
- `Initial Build Development Context.md` is now local-only. Anything that
  needs its content must read it from the working tree or `.backups/`.
- `.backups/` holds the only copies of the two build-notes files purged from
  history, alongside the pre-rewrite bundle. Do not clear the directory
  wholesale when deleting the bundle.

---

## Where things live

| Concept | File |
|---|---|
| Privacy check | `scripts/check_personal_exposure.py` |
| Portable version of the check | `.claude/skills/business-name-privacy-check/` (local only) |
| Heat gradient, pin colors, light/dark switch | `src/step5_map.py` |
| Personal-name disclosure | `pages/3_Methodology_&_Limitations.py`, Limitations |
| Dependency bounds | `requirements.txt` |
| Reasoning and exact values | `docs/DECISIONS.md`, entries dated 2026-09-20 |
| Visual work from earlier the same day | `docs/Visual Design & Heatmap Review.md` |
| Source licenses and terms | `docs/data_sources.md` |
| Attribution, and Sound Transit's flow-down terms | `pages/3_Methodology_&_Limitations.py`, Data Sources |
| Pre-rewrite history, build notes | `.backups/` (local only) |
