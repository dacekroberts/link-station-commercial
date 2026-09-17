# Sessions 1-7 Context

Written 2026-09-13, at the end of Session 7, as a context-preservation
checkpoint ahead of a likely conversation compaction. Purpose: let a new
Claude session (or the user) reconstruct full working context fast, without
re-deriving anything already settled. **This is a summary, not the record of
truth** — `DECISIONS.md` is authoritative for exact numbers and reasoning;
`PLAN.md` has the session-by-session checklist; this document is the fast
map between them.

---

## The project, one paragraph

Measures commercial density in concentric rings (0.1/0.2/0.3/0.6 mi) around
the 16 Link 1 Line stations inside Seattle city limits, tests whether
density falls off with distance from the platform, and asks whether that
says anything about how businesses choose locations near transit. Three
analyses: distance gradient, ridership-vs-density relationship, chain
footprint. Deliverable: a 3-page Streamlit site (heatmap, findings,
methodology), aimed at hiring managers, as a portfolio piece. User has
introductory Python, no GIS background — explanations have been part of the
work throughout, not just code.

## Who's who

- User: `dacekroberts@gmail.com`, GitHub `dacekroberts` (renamed from
  `tykwondo` on 2026-09-17; all local commit history rewritten to match -
  see `DECISIONS.md`). Git identity is **repo-local**, not global:
  `dacekroberts` / `49654908+dacekroberts@users.noreply.github.com` (a
  GitHub noreply address, chosen deliberately so commits attribute to the
  account with zero personal email exposed in history).
- Repo: `C:\Users\dacek\Documents\Portfolio\link-station-commercial`, git
  initialized Session 1, on `main`, no remote yet (Session 9 territory).

## Architecture invariants (do not relitigate)

- **Pipeline (`src/`) writes `outputs/`; the Streamlit app (`app.py`,
  `pages/`) only reads `outputs/`.** Nothing else crosses that boundary.
  `requirements.txt` is deliberately lean (streamlit, pandas) because
  Streamlit Cloud installs from it; the geo stack lives in
  `requirements-pipeline.txt`, local-only.
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
- Never write the interpretive prose in `pages/2_Findings.py`'s three
  `TODO` blocks — that's the user's analysis and the point of the project.

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
`step4_rings.py` and `pages/2_Findings.py`.

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
Current file size ~3.2 MB.

---

## Current pipeline state (as of end of Session 7)

| Stage | File | Rows | Committed? |
|---|---|---|---|
| Stations | `data/processed/stations.csv` | 16 | No (gitignored, regenerable) |
| Clean businesses | `data/processed/businesses_clean.csv` | 11,466 | No |
| Geocoded businesses | `data/processed/businesses_geocoded.csv` | 11,409 | No |
| Ridership | `data/raw/ridership_by_station.csv` | 16 | No (raw download, gitignored) |
| Ring stats | `outputs/ring_stats.csv` | — | **Yes** |
| Station stats | `outputs/station_stats.csv` | 16 | **Yes** |
| Chain stats | `outputs/chain_stats.csv` | 3,907 brands | **Yes** |
| Heatmap | `outputs/heatmap.html` | 11,409 points | **Yes** |

All five pipeline scripts (`step1` through `step5`) run clean end to end
with zero warnings on the current data. Streamlit app boots and all 4 pages
render (verified via `streamlit.testing.v1.AppTest` repeatedly through the
project, and via an actual running app + browser check for the map
specifically).

## What's NOT done yet

- **Session 8 — the write-up.** The three `TODO` prose blocks in
  `pages/2_Findings.py` (gradient interpretation, ridership interpretation,
  chain interpretation) are the user's to write, not Claude's — this is
  the one firm rule that's held throughout. Also: resolve remaining
  `[FILL IN]`/placeholder text in `pages/3_Methodology.py` if any are left
  (most were already resolved incrementally through Sessions 1-7), transfer
  the `DECISIONS.md` record into the methodology page's prose, trim
  limitations to what's actually true for this run, rewrite `app.py`'s
  intro to state what was actually found.
- **Session 9 — deploy.** No GitHub remote yet. Push to a public repo,
  confirm `outputs/` is committed and `requirements.txt` stays lean, deploy
  on Streamlit Community Cloud, verify all pages on the live URL.

## Where to look for what

- **`DECISIONS.md`** — the authoritative, detailed record. Has a "Changes"
  log (macro-level, newest-first) at the top, then full sections:
  Environment, Data provenance, Analyst choices, Quality metrics
  (geocoding/rings/chain-bug detail), **Map rendering** (all of Session 7's
  map work, kept current across multiple rounds of changes), Observations
  (Session 6's four-part write-up), Things that went wrong, Open items.
- **`PLAN.md`** — the session-by-session checklist, updated with `[x]`/DONE
  markers and actual-vs-planned notes as each session closed.
- **`initialscript.md`** — the original project briefing; also kept
  current (NE 130th status, resolved unknowns, etc.) rather than left
  stale.
- **`config.py`** — every tunable, with reasoning in comments:
  `NAICS_STOREFRONT_PREFIXES`/`_EXCLUDE`/`_REVIEWED_KEPT`,
  `SEATTLE_1LINE_STATIONS`, ring edges, CRS constants, `GEOCODE_*` and
  provenance-string constants the methodology page reads.
- **`CLAUDE.md`** — the condensed project-conventions file, includes the
  business-license-source invariant explicitly (don't swap the pipeline to
  the GIS layer as primary).
