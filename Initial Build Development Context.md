# Initial Build Development Context

Written 2026-09-13 at the end of Session 7, extended 2026-09-17 at the end
of Session 9 to cover Sessions 8 and 9 and merged into one document — a
context-preservation checkpoint covering the project's entire initial
build, Sessions 1 through 9. Purpose: let a new Claude session (or the
user) reconstruct full working context fast, without re-deriving anything
already settled. **This is a summary, not the record of truth** —
`DECISIONS.md` is authoritative for exact numbers and reasoning; `PLAN.md`
has the session-by-session checklist; this document is the fast map
between them.

---

## The project, one paragraph

Measures commercial density in concentric rings (0.1/0.2/0.3/0.6 mi) around
the 16 Link 1 Line stations inside Seattle city limits, tests whether
density falls off with distance from the platform, and asks whether that
says anything about how businesses choose locations near transit. Three
analyses: distance gradient, ridership-vs-density relationship, chain
footprint. Deliverable: a 5-page Streamlit site (overview, heatmap,
findings, methodology, flowchart), aimed at hiring managers, as a
portfolio piece — deployed and live since Session 9. User has introductory
Python, no GIS background — explanations have been part of the work
throughout, not just code.

## Who's who

- User: `dacekroberts@gmail.com`, GitHub `dacekroberts` (renamed from
  `tykwondo` on 2026-09-17; all local commit history rewritten to match -
  see `DECISIONS.md`). Git identity is **repo-local**, not global:
  `dacekroberts` / `49654908+dacekroberts@users.noreply.github.com` (a
  GitHub noreply address, chosen deliberately so commits attribute to the
  account with zero personal email exposed in history).
- Repo: `C:\Users\dacek\Documents\Portfolio\link-station-commercial`, git
  initialized Session 1, on `main`, public at
  `github.com/dacekroberts/link-station-commercial` since Session 9.
  Deployed on Streamlit Community Cloud, main file
  `Overview_&_Introduction.py` (renamed from `Introduction.py` later in
  Session 9 — see below).

## Architecture invariants (do not relitigate)

- **Pipeline (`src/`) writes `outputs/`; the Streamlit app
  (`Overview_&_Introduction.py`, `pages/`) only reads `outputs/`.** Nothing
  else crosses that boundary. `requirements.txt` is deliberately lean
  (streamlit, pandas, altair) because Streamlit Cloud installs from it; the
  geo stack lives in `requirements-pipeline.txt`, local-only.
- **`outputs/` is committed to git** — the deployed app can't regenerate it.
- **CRS rule**: never buffer/measure distance in EPSG:4326 (degrees).
  Project to EPSG:32610 (UTM 10N, metres), do the geometry, reproject back
  to 4326 for display. A straight coordinate *transform* (not buffering) in
  4326 is fine — e.g. reading raw lat/lon from a source CRS and reprojecting
  once.
- **Rings are annuli** — each subtracts the disc inside it, or the gradient
  is meaningless.
- Scope is locked: Seattle 1 Line only (Northgate-Rainier Beach, 16
  stations), business licenses not OSM, ridership manually transcribed not
  automated, overlapping downtown buffers allowed and disclosed rather than
  corrected.
- Never write the interpretive prose in `pages/2_Findings_&_EDA.py`'s
  `TODO` blocks — that's the user's analysis and the point of the project.
  (Moot as of Session 8: all three blocks are filled with the user's own
  drafted prose. The rule still governs any future analysis writing.)
- **The site is dark-theme-only as of Session 9** (`.streamlit/config.toml`,
  `[theme] base = "dark"`). Once a developer sets an explicit theme,
  Streamlit removes its own light/dark toggle from the UI — there is no
  in-app way for a visitor to get light mode back.

## Environment

- Python **3.12.14** via `uv`, not the system default (3.14, too new for
  compiled geo-stack wheels) and not 3.11 (the `py` launcher's registered
  3.11 pointed at a deleted install). `.venv` at repo root holds both
  `requirements.txt` and `requirements-pipeline.txt` installed together
  locally (the lean/heavy split still matters for what Streamlit *Cloud*
  installs, just not for the local dev venv).
- No conda needed. `.gitattributes` normalizes line endings to LF (verified
  zero collateral — blobs were already LF via `core.autocrlf=true`).

---

## Session-by-session recap

### Session 1 — Environment & data
venv/toolchain set up (see above). All manual downloads done: `gtfs.zip`,
`business_licenses.csv` (84,390 rows, City of Seattle, dataset `wnbq-64tb`,
downloaded 2026-09-06), plus two extras the user's own research turned up:
`business_licenses_geocoded.geojson` (the "Seattle Business License" GIS
layer, 54,443 pre-geocoded points) and `st_gis_shapefiles.zip` (contains
`LINKStations.shp`, a station-point fallback never actually needed).

**Key decision: CSV is the canonical business-license source; the GIS layer
is a geometry donor only**, never primary. Reasoning: the GIS layer silently
omits ~10% of Seattle businesses (the ones its own geocoder couldn't place)
with no way to characterize the gap — the same class of coverage-bias
problem that got OpenStreetMap rejected in the original scope decision.
Starting from the CSV and geocoding it ourselves (Session 4) makes every
drop visible and reportable. This is `NAICS_STOREFRONT_...`-adjacent logic
recorded in `config.py` comments and `CLAUDE.md`'s own invariants list now.

`COLUMN_MAP` in `step2_clean_businesses.py` filled from the confirmed
headers (pulled forward from its originally-planned Session 3 slot).
`LICENSE_SNAPSHOT = "2026-09-06"`.

### Session 2 — Station coordinates
`step1_stations.py` had a real bug: `ROUTE_NAME_PATTERN` substring-matched
both the real train (route_id `100479`, short_name "1 Line") and a bus
shuttle bridge route (`1-SHUTTLE`, long_name "1 Line Shuttle Bus"),
producing 17 "stations" including 3 bogus bus-stop duplicates of SODO.
Fixed to exact match on `route_short_name`. Also added `GTFS_NAME_ALIASES`
for two GTFS abbreviations ("Univ of Washington" -> canonical "University
of Washington", "Int'l Dist/Chinatown" -> "International
District/Chinatown"). Result: **16 of 16 stations resolved, zero
unmatched-name warnings**, coordinates spot-checked. **NE 130th/Pinehurst
confirmed absent** from this GTFS snapshot (feed dated 2026-08-28) — stays
out of scope, 16 stations as planned. `data/processed/stations.csv` is the
output (gitignored, regenerable).

Also measured (used later, Session 6): platform-to-averaged-station-point
offset, 14 m (Capitol Hill) to 72 m (Columbia City), mean 48 m — not
negligible against the 161 m innermost ring, documented on the methodology
page.

### Session 3 — Clean the business data
Wired the deferred step-2 work: filter to `City == "SEATTLE"` (~30% of the
CSV is non-Seattle addresses — a factual correction to the original
"dataset stops at the city line" assumption, fixed in every doc that
repeated it), dedupe on City Account Number (not UBI, 8.3% blank), carry
account number + license start date through.

**NAICS filtering, the most consequential judgment call in the project.**
Prefix list stayed `44, 45, 722, 812`. Two individual NAICS codes excluded
after hand-sampling, both recorded with full reasoning in `config.py`
(`NAICS_STOREFRONT_EXCLUDE`) and rendered live on the methodology page:
- `812930` Parking Lots and Garages (826 rows) — a planned trip decision,
  not the incidental foot traffic this analysis measures.
- `812990` All Other Personal Services (2,424 rows) — NAICS's residual
  catch-all; a 40-row hand sample found ~90% non-storefront (home-based sole
  proprietors, professional offices, come-to-you services).

One category was reviewed the same way and **kept**: `459999` All Other
Miscellaneous Retailers (1,190 rows) — retail's own catch-all, but a 25-row
sample found ~70% plausible storefronts (niche independent shops without
their own code). Recorded in `config.py`'s `NAICS_STOREFRONT_REVIEWED_KEPT`,
juxtaposed with the exclusions on the methodology page so "checked and
fine" is as visible as "checked and dropped."

Also fixed at the source (raw 84,390-row file, not just the filtered set):
22 blank `business_name` rows (fell back to Legal Name), 5 `19000101`
null-date sentinels in `license_start_date` (nulled, not dropped).

**Final clean count: 11,466 businesses** (84,390 -> 58,774 Seattle ->
14,728 NAICS-prefix -> 13,902 minus parking -> 11,478 minus personal-svc
catch-all -> 11,466 after dedup/address-validity).

### Session 4 — Geocode
Wired the GIS-donor join scoped back in Session 1: left-join geometry from
the GeoJSON by City Account Number (reprojecting its `EPSG:2926` directly to
`EPSG:4326`), send only the unmatched remainder to the Census bulk
geocoder. Results: **donor join 90.2%** (10,345/11,466), **Census on the
1,121-row remainder 94.9%** (1,064/1,121), **overall 99.5%**
(11,409/11,466). Well above the 75% bail-out; no `usaddress` parsing needed.
`geocode_source` column (`donor`/`census`) carried through for traceability.
Spot-checked 5 points per source against Google Maps.

New `config.py` constants: `GEOCODE_DONOR_MATCHED`, `GEOCODE_CENSUS_MATCHED`,
etc. — the methodology page reads these rather than computing at runtime
(the app only sees `outputs/`, and `data/processed/` doesn't exist on
Streamlit Cloud).

`data/processed/businesses_geocoded.csv` is the output (gitignored,
regenerable) — **11,409 rows**, this is what `step4_rings.py` and
`step5_map.py` both consume.

### Session 5 — Ridership
**Reconfigured mid-session from one month to a full year**, at the user's
initiative: rather than a single Power BI export, all twelve months of 2025
were captured as dashboard screenshots, collected into a Google Doc,
exported as PDF, and transcribed (via PyMuPDF, since the Read tool's PDF
path needed `poppler`, not installed). Still fully manual — no automation
of the Power BI embed, just more manual reads. Averaging a year smooths
seasonality better than one arbitrary month.

**Metric decision, checked not assumed.** The dashboard also showed an
"average boardings per day" figure. First assumed to be a trivial
`total ÷ days-in-month` derivation and therefore skippable as redundant —
**checked against all 192 station-months and that assumption was wrong**:
it matches neither `total ÷ calendar days` nor `total ÷ weekdays` (off by
roughly +9%/-22% on average), so Sound Transit applies its own service-day
weighting. It's still not transcribed, but on different, verified grounds:
averaged to one figure per station across the year, the two metrics
correlate at **r = 0.998** across all 16 stations — close enough to
redundant for a cross-station comparison that transcribing both wouldn't
change the analysis.

Final column: `avg_monthly_boardings` (average of 12 monthly totals,
weekend-inclusive — deliberately not the industry-standard "average weekday
boardings," since weekday ridership is commute-skewed and would understate
exposure to the retail/food storefronts this project measures).
`RIDERSHIP_SNAPSHOT = "Jan-Dec 2025 (average of monthly totals)"`.

**16 of 16 station names matched `stations.csv` exactly**, zero missing,
zero extra. `data/raw/ridership_by_station.csv` is the output (gitignored,
matches the "manual download" pattern of the other raw files).

**Found while transcribing**: Stadium's April 2025 (193,465 total
boardings) is a genuine outlier, 3-9x every other month for that station —
likely a Mariners early-season surge (Stadium sits at T-Mobile
Park/Lumen Field). Kept in the average like any other month, flagged for
Session 6.

### Session 6 — Rings, and the first real numbers
`step4_rings.py` run end to end: 16 stations, 11,409 businesses, **6,847
business-ring matches**, zero unmatched-station warnings anywhere.

**Found and fixed a real bug via the plan's required "verify a handful by
hand" step on the chain analysis.** The original chain definition
(`station_count > 1`) is inflated by the same downtown buffer overlap
already disclosed for density: a single physical location inside the
4-station overlap zone (Westlake/Symphony/Pioneer Square/International
District) can register as "present at 4 stations" without being a chain at
all. Two real examples (PU POWDER, Saigon Drip Kitchen, each one location)
surfaced this directly; checked systematically, **1,589 of 3,907 normalized
brands (41%)** show the pattern. Cost of the bug: `station_count > 1` would
have reported **45.7%** of locations as chains; the correct
`location_count >= 2` definition puts the true figure at **8.8%** — a >5x
overstatement that would have been a headline Findings number. Fixed in
`step4_rings.py` and `pages/2_Findings_&_EDA.py`. (Later refined further in
Session 7/8 — see the corporate-food-service-contractor exclusion below;
final figure **152 brands, 8.5%**.)

**Gradient**: not monotonic. Aggregate density by ring: 957 -> 550 -> **592**
-> 311 businesses/sq mi (a real ring-3 uptick). Traced to a specific,
checkable cause, not left as a mystery: Symphony and Westlake sit 0.268 mi
apart — closer together than the ring system's own 0.6 mi reach — so each
one's outer rings partly sample the *other's* dense core rather than
measuring only their own periphery. Effect scales with inter-station
distance (weak at Beacon Hill/Mount Baker, 0.659 mi apart), which is itself
evidence the mechanism is real. One exception the mechanism doesn't
explain: Pioneer Square's ring1->ring2 rise, left as an open question
(probably a genuine siting effect, its commercial core sitting slightly off
from the platform).

**Stations against the pattern**: Rainier Beach (literal zero in the
0.2-0.3mi ring specifically), SODO (density rises through rings 1-3 before
falling — industrial at the platform, real commerce toward Pioneer Square's
edge), Stadium (1 business in ring 1, 373 in ring 4 — mostly borrowed from
International District/Chinatown 0.416 mi away). Also, not named in the
original plan but found independently: **Northgate and University of
Washington both have zero businesses in the entire 0-0.1mi ring.**

**Ridership relationship**: r = 0.684 (n=16). University of Washington is
the sharpest outlier — lowest density of any station (5 businesses within
0.3mi) but 5th-highest ridership (152,748/month), consistent with a
campus/hospital population that rides without shopping nearby.

Full Observations write-up (all four sections, not trimmed to three) is in
`DECISIONS.md`.

### Session 7 — The map
Ran `step5_map.py`, then found and fixed real problems, not just
cosmetics:

1. **CartoDB Positron (the originally intended basemap) is dead** — now
   requires an API key. Tested and rejected Esri's free "World Light Gray"
   alternative too (legacy/deprecated status, non-commercial-only terms —
   same fragility class that just broke CartoDB). Landed on **OpenStreetMap**
   tiles — busier, but a long, stable free-use track record.
2. **A known, still-open Leaflet.heat bug**
   (github.com/Leaflet/Leaflet.heat/issues/95) was silently breaking the
   *entire* map, not just the heat layer — an uncaught `IndexSizeError` on
   init (map container size not resolved yet) stopped every subsequent
   `.addTo(map)` call in the generated script, so rings/stations/layer
   control never rendered. Fixed with fixed pixel map dimensions
   (`width=1000, height=650`) instead of percentage-based sizing.
3. Heat layer tuned via a real 3-way visual comparison (not guessing):
   `radius=8, blur=10, min_opacity=0.35` (was 12/18/0.3) — keeps
   neighbourhood clusters distinguishable at the default city-wide zoom.

**Added, beyond the original plan, across several rounds of user requests:**
- Per-business pin layers, clustered (`FastMarkerCluster` — required at
  11,409 points, not optional) and color-coded by the same three NAICS
  groups `config.py` already defines (Retail 44/45 blue, Food service 722
  orange, Personal services 812 teal — 5,221/3,909/2,279, no "Other"
  bucket needed), with a legend.
- **Considered and explicitly declined** a dynamic, JS-driven NAICS-code
  filter (a dropdown reconfiguring the map on the fly) as out of proportion
  this late — new untested JS complexity for a polish feature, while
  Session 8's write-up is the actual highest-value time left. Built the
  cheaper version instead: 12 finer static toggle layers within the 3 broad
  groups (real top categories by count — e.g. Full-service/Limited-service/
  Mobile-food within Food service), reusing the identical proven pattern.
- The real 1 Line rail alignment from GTFS `shapes.txt` (shape_id
  `N23:S07`, 1,204 points — the actual curved route, not a straight line
  between stations), solid green, on by default, with a large always-visible
  label (went through several placement iterations before landing clear of
  the UI, west of the downtown corridor per the user's specific ask).
- Richer hover tooltips on business pins: name, NAICS code, nearest station,
  and ring band relative to that station (a deliberately separate, simpler
  computation from `step4_rings.py`'s overlap-aware `ring_stats` — built
  only for the tooltip).
- Hover tooltips on station markers too: name + 2025 avg monthly ridership,
  reusing `ridership_by_station.csv` directly.
- Layer control collapsed by default (23 toggleable layers had grown it
  large enough to cover most of the map) with a CSS max-height/scroll cap —
  Leaflet's own built-in collapsed state, not a custom control.
- Fixed a couple of small real bugs the user caught by reading the actual
  UI text: an ambiguous "Retail (44/45)" legend label sitting next to a
  business count also in parens (now spells out "NAICS Code:"), and a
  doubled category name in the three whole-group business layer names
  ("Retail — Retail — NAICS Code: 44/45" -> "Retail — NAICS Code: 44/45").

`outputs/heatmap.html` is committed (per the "outputs/ is committed" rule).

### Session 8 — Write it up
The highest-value hours in the project: filled the three `TODO` prose
blocks in `pages/2_Findings_&_EDA.py` with the user's own drafted,
fact-checked prose (gradient per-station notes and Concluding Thoughts,
ridership Graph 3/Table 2 plus a new Graph 4 dot-plot/Table 3
coefficient-of-variation write-up built from scratch, and the chains
section below Table 4 and Graph 5). `pages/3_Methodology_&_Limitations.py`
was not just filled in but rewritten wholesale in the user's own
first-person voice, with `DECISIONS.md` content transferred over
(Method rationale, Data Sources, NAICS filtering reasoning, all five
Limitations subsections, "What a Fuller Version Would Add") — environment
setup and the session-by-session "things that went wrong" log stayed
in `DECISIONS.md`/this document as project history, not reader-facing
methodology. Limitations were re-verified twice, including catching the
chain-overlap numbers drifting stale (155/8.9% → corrected to 152/8.5%)
via a fresh pipeline run.

`Introduction.py` (pre-rename) got a new "What I Found" section between
"What's here" and "Why Seattle?": four bulleted headline findings (the
~67.5% ring 1->4 decline with the real ring-3 anomaly, r=0.684 ridership
correlation, the 1.8x businesses-vs-ridership variance gap, chain share
highest at the platform), each number verified against the live pipeline
output before shipping.

**Beyond the original plan:** site-wide polish (GitHub/LinkedIn icon links
and a narrower sidebar on every page), a base site font (Inter) applied to
page text site-wide (explicitly excluding chart/diagram text), and a 5th
page (`pages/4_Flowchart.py`) showing the pipeline's real build process as
a Mermaid diagram with two decision diamonds — one for the chain-definition
bug catch (Session 6), one for the basemap/heat-layer saga (Session 7).
30 commits, each change committed individually.

**Also this session:** three corporate food-service contractors (Compass
One, Bon Appétit Management, Flik International) excluded from chain
analysis only, not density — each is one vendor operating cafeterias
across a client company's own buildings, not an independent chain making
its own repeated real-estate decisions. Caught when the user noticed
Compass One's 11-location count looked suspicious while reviewing the
chains table. Identified via NAICS 722310 (Food Service Contractors)
co-occurrence, but filtered by the three specific brand names rather than
the NAICS code directly (722310 alone only tags 1 of Compass One's 24
records). Final chain headline: **152 brands, 8.5% share** (moved from
155/8.9%).

### Session 9 — Deploy, then a full day of polish

Scoped as "Deploy" in `PLAN.md`. Did that in the first hour, then kept
going for the rest of the day into a long, unplanned polish pass driven by
the user actually using the live deployed site and finding things worth
changing.

**Deploy.** Pushed the repo to a new public GitHub repo,
`github.com/dacekroberts/link-station-commercial`, then deployed on
Streamlit Community Cloud. Key mental model established for the user:
**commit is local, push is live.** A local `git commit` only saves to the
local repo; only `git push` to the tracked remote actually updates the
deployed site. Streamlit Cloud watches the GitHub `main` branch via
webhook and rebuilds within seconds of any push — no manual redeploy step
after initial setup. **Pipeline-change vs. app-change workflow**: app/page
code changes just need commit+push; pipeline (`src/step*.py`) changes
require rerunning the affected step(s) locally in `.venv` first to
regenerate `outputs/*.csv`/`heatmap.html`, *then* committing both the
script and the regenerated outputs, then pushing — Streamlit Cloud never
executes pipeline scripts itself. A commit landed directly on GitHub's web
UI (`.devcontainer/devcontainer.json`) while the deploy was in progress,
causing one `git push` rejection; resolved cleanly with `git fetch` +
`git pull --rebase` + `git push`.

**Production bug found by actually browsing the live site.** Browsing the
freshly deployed app surfaced a real `FileNotFoundError` on the Findings &
EDA page: it read `data/processed/stations.csv` directly for Table 1's
station ordering — a gitignored pipeline intermediate that only "worked"
locally because it happened to still be on disk from that day's earlier
pipeline run, and doesn't exist on a fresh Streamlit Cloud checkout. A
genuine violation of the project's own core invariant. Fixed by switching
to `SEATTLE_1LINE_STATIONS`, a pre-existing `config.py` constant already
in the correct order. Verified rigorously by temporarily hiding
`data/processed/` entirely to reproduce Streamlit Cloud's real file layout
before trusting the fix, rather than just trusting a local server that
would have kept "working" anyway even with the bug present. **Lesson for
future sessions**: local testing can silently mask this exact class of
bug — when in doubt whether a page reads only from `outputs/`, temporarily
move `data/processed/` aside and reload before trusting a "looks fine
locally" result.

**AI Use section.** Added a short, collaboratively drafted disclosure on
the Methodology page: five Skilljar courses on Claude Code completed
before starting, then Claude Code used throughout for pipeline scripts,
the Streamlit pages, and bug-catching — with the analysis, interpretation,
and judgment calls stated explicitly as the user's own.

**Findings & EDA page, visual pass.**
- Added a concentric-ring schematic ("Schematic 1") beside Graph 1 and
  Graph 5, iterated live in chat before touching any files: ended as a
  compact vertical layout with four categorically distinct colors
  (green/blue/purple/teal for rings 1-4), explicitly avoiding red/orange
  since those colors are already used elsewhere on the page. Graph 1 and
  Graph 5's bars recolored to match, so the schematic reads as a legend
  for the bars.
- **Real bug hit and fixed:** the schematic's SVG, embedded via
  `st.markdown(..., unsafe_allow_html=True)`, initially had blank lines
  between element groups. Streamlit's markdown renderer follows
  CommonMark's rule that a generic raw-HTML block ends at the first blank
  line — everything after was silently dropped. Fixed by collapsing the
  SVG into one unbroken string.
- Horizontal x-axis labels on Graphs 1, 2, and 5 (previously rotated).
  Forcing `labelAngle=0` alone triggered Vega-Lite's own overlap-avoidance
  to silently hide two of four ticks; fixed with a `labelExpr` showing
  just "Ring N" on the axis, full range still in the tooltip.
- A "How to read this chart" `st.popover` added to Graph 3, matching
  Graph 4's existing one. Graph 4's `0.0` x-axis tick renamed to "Mean"
  (needed explicit coarser axis `values` since the default step packed in
  enough ticks that Vega's overlap-avoidance was dropping that exact one).
  Bolding just that tick was investigated and found not possible in this
  Altair/Vega-Lite version (`alt.Axis` has no `encode` property, confirmed
  via `SchemaValidationError`) — left un-bolded rather than bolding every
  tick as a workaround.
- Added an "In Summary" section at the very end of the page, plus dividers
  above "Ridership Analysis"/"Chain Analysis" (none existed between the
  page's three major sections before today).

**Heatmap page.**
- Stations and the Link 1 Line route made permanently visible
  (`control=False`) instead of togglable layers — baseline map context,
  not something a reader would want to hide.
- Default-checked layers changed to: the within-proximity heat layer, all
  four concentric rings (was only Ring 3), and the three broad NAICS-group
  pin layers (was none). New `show` parameter threaded through
  `add_pin_layer()`.
- **Real bug found and fixed: cluster hover-blocking.** A business dot was
  unhoverable because a nearby cluster's icon hit area covered it, even
  though the cluster looked visually small. Root cause: Leaflet.markercluster's
  default `iconCreateFunction` gives every cluster the same fixed 40×40px
  icon regardless of point count — a 2-point cluster gets exactly as large
  a hit area as a 500-point one. Fixed with a custom `icon_create_function`
  passed to `FastMarkerCluster` (confirmed via `inspect.signature` that
  this parameter exists and passes straight through to the underlying
  `L.markerClusterGroup()` JS options) scaling icon size by child count:
  18px for ≤3, 26px for ≤10, 34px for ≤50, 42px above that. Verified in the
  live DOM: 2-3 point clusters now measure exactly 18×18px versus 10px
  individual dots. Also colors each cluster badge to match its own NAICS
  group's dot color.
- The layer-control passage underlined and reworded, with the map's own
  layer-control icon appended after it (fetched once, inlined as a base64
  `data:` URI to avoid a live network fetch). Legend header capitalized
  ("Business category" → "Business Category").

**Overview & Introduction: rename + new section.** Renamed
`Introduction.py` → `Overview_&_Introduction.py` (`git mv`, preserving
history). This is the app's actual entry point — what `streamlit run`
targets and what Streamlit Cloud's "main file path" setting points at —
so unlike the earlier `app.py`→`Introduction.py` and Findings/Methodology
renames, **the Streamlit Cloud app had to be deleted and recreated**
pointing at the new filename; that setting can't be edited in place
post-creation. Updated every other live reference to the old filename
(`CLAUDE.md`, `README.md`, `.devcontainer/devcontainer.json`,
`.claude/launch.json`); left `PLAN.md`'s completed checklist items and
this document's own earlier (pre-merge) text alone, per the established
renaming precedent. Added a new "Overview" section right after the byline:
three short bullet-point columns separated by vertical dividers, built
with real `st.columns(3)` (not raw HTML divs, so it still stacks
correctly on mobile) wrapped in `st.container(key="overview_columns")` so
the injected divider CSS only targets this one row of columns.

**Dark theme lock.** Added `.streamlit/config.toml` with
`[theme] base = "dark"`. **Real finding:** once a developer sets an
explicit `[theme]`, Streamlit removes its own light/dark toggle from the
UI entirely (checked the full "Main menu" — no Settings/theme entry
exists anymore). The app is now dark-only for every visitor, with no
in-app escape hatch — which is why two other hardcoded-dark spots (Graph
2's legend `fillColor`, the Flowchart page's Mermaid theme) were
deliberately left as-is rather than made "dynamic": there's no reachable
light mode left to dynamically match against.

**Sitewide Grammarly copy pass.** The user ran every page's visible prose
(excluding captions, tooltips, and embedded graph/table text) through
Grammarly externally, then pasted the edited text back per-page. Applied
across six files by diffing each pasted paragraph against the live source
and applying only the actual deltas — mostly punctuation, capitalization,
and small word-choice fixes — preserving every f-string variable, HTML
tag, and code structure untouched. Two incidental real bugs surfaced and
got fixed along the way: `config.py`'s `LICENSE_SOURCE` constant ended in
a period that collided with the Methodology page's own template
punctuation right after it (rendering as "...match., downloaded
2026-09-06"), fixed on both ends; and several NAICS/chain-exclusion reason
strings in `config.py` used em dashes, replaced with comma/period/
semicolon phrasing for consistency. One pasted fragment was deliberately
**not** applied — bare hyphens glued to words with no surrounding spaces,
which read as a paste artifact and contradicted the user's own explicit
"no em dashes" instruction for that exact passage — left as-is and
flagged instead of guessed.

**Smaller copy fixes:** "Methodology & Limitations" decapitalized in the
Overview page's "What's here" paragraph; "The same study" → "The Yang and
Diez-Roux study" on the Methodology page; the Flowchart page's
pivot-points paragraph reworded to point at the diagram's own diamond
shapes; the README's "Two things that will bite" section removed.

**Pipeline re-verified.** Re-ran `step1` through `step5` once, purely to
confirm the day's `step5_map.py` changes hadn't broken anything upstream.
All five steps ran clean with zero warnings, every figure matched the
already-committed baseline exactly. `outputs/heatmap.html` showed a git
diff after regenerating but was confirmed byte-identical to the committed
version once Folium's random per-render element IDs were normalized out —
reverted that cosmetic no-op rather than committing it.

---

## Current pipeline state (as of end of Session 9)

| Stage | File | Rows | Committed? |
|---|---|---|---|
| Stations | `data/processed/stations.csv` | 16 | No (gitignored, regenerable) |
| Clean businesses | `data/processed/businesses_clean.csv` | 11,466 | No |
| Geocoded businesses | `data/processed/businesses_geocoded.csv` | 11,409 | No |
| Ridership | `data/raw/ridership_by_station.csv` | 16 | No (raw download, gitignored) |
| Ring stats | `outputs/ring_stats.csv` | — | **Yes** |
| Station stats | `outputs/station_stats.csv` | 16 | **Yes** |
| Chain stats | `outputs/chain_stats.csv` | 3,900 brands | **Yes** |
| Heatmap | `outputs/heatmap.html` | 11,409 points | **Yes** |

All five pipeline scripts (`step1` through `step5`) run clean end to end
with zero warnings on the current data, re-verified as recently as the end
of Session 9. The Streamlit app is live on Streamlit Community Cloud, all
5 pages verified on the deployed URL.

## What's left

Sessions 1 through 9 — the entire originally-planned build, through
deploy — are done. There is no outstanding "next session" on the books.
Anything from here is net-new scope, not a gap in the original plan. A few
things flagged along the way that were deliberately deferred rather than
done, in case they come up again:
- A dynamic, JS-driven NAICS-code filter dropdown for the heatmap
  (considered and declined in Session 7 as disproportionate polish).
- The "What a Fuller Version Would Add" list on the Methodology page
  (control corridors, the 2 Line, a before-and-after design, continuous
  distance-decay weighting) — documented as real, scoped-out extensions,
  not bugs or gaps.
- Centered `st.dataframe` table headers on the Findings page (investigated
  in a later session; not possible without switching to `st.table`, which
  loses scrolling/resizing/sorting — left as `st.dataframe` with
  left-aligned headers per explicit user choice).

## Things worth remembering going into future sessions

- **Streamlit's raw-HTML markdown blocks end at the first blank line**
  (CommonMark rule) — any multi-element HTML string passed to
  `st.markdown(..., unsafe_allow_html=True)` needs to be one unbroken
  block, no blank lines between tags, or content after the first blank
  line silently vanishes.
- **`st.dataframe` cannot have its headers styled** — it renders through a
  single `<canvas>` element, so header text is pixels, not DOM text, and
  no CSS or Styler rule can reach it. `st.table` uses real `<th>` DOM
  elements and *can* be styled, but loses scrolling/resizing/sorting.
- **A forced `[theme]` in `config.toml` removes Streamlit's own theme
  toggle from the UI.** There is no partial version of this — it's
  all-or-nothing once set.
- **`FastMarkerCluster` accepts `icon_create_function` and `options`**
  (both pass straight through to the underlying `L.markerClusterGroup()`
  JS) — useful for any future Leaflet.markercluster tuning.
- Local deploy verification generally used a persistent scratchpad venv
  (`deploy-venv`, built from `requirements.txt` only, no pipeline deps) on
  incrementing ports, restarted fresh (kill process + clear `__pycache__`)
  before every check that touched shared modules like `components.py` —
  Streamlit's rerun can otherwise serve a stale cached version of a shared
  import without a full process restart. Page-level (`pages/*.py`) changes
  don't have this issue and reload correctly on a simple navigate/rerun.

## Where to look for what

- **`DECISIONS.md`** — the authoritative, detailed record. Has a "Changes"
  log (macro-level, newest-first) at the top, then full sections:
  Environment, Data provenance, Analyst choices, Quality metrics
  (geocoding/rings/chain-bug detail), Map rendering, Observations
  (Session 6's four-part write-up), Things that went wrong, Open items.
- **`PLAN.md`** — the session-by-session checklist, updated with `[x]`/DONE
  markers and actual-vs-planned notes as each session closed.
- **`initialscript.md`** — the original project briefing; also kept
  current (NE 130th status, resolved unknowns, etc.) rather than left
  stale.
- **`config.py`** — every tunable, with reasoning in comments:
  `NAICS_STOREFRONT_PREFIXES`/`_EXCLUDE`/`_REVIEWED_KEPT`,
  `CHAIN_ANALYSIS_EXCLUDE_BRANDS`, `SEATTLE_1LINE_STATIONS`, ring edges,
  CRS constants, `GEOCODE_*` and provenance-string constants the
  methodology page reads.
- **`CLAUDE.md`** — the condensed project-conventions file, includes the
  business-license-source invariant explicitly (don't swap the pipeline to
  the GIS layer as primary).
