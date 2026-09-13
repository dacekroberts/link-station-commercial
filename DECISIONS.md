# Decisions log

Every judgment call, recorded when you make it. The methodology page is
assembled from this file, and reconstructing these choices a week later is
guesswork.

Format: what you chose, why, and what it rules out.

---

## Changes

Macro-level deviations from the original project design, newest first. One line
each; detail lives in the sections below.

### 2026-09-13 — Session 6

- Ran `step4_rings.py` end to end: 6,847 business-ring matches, 16 of 16
  stations resolved with zero unmatched-name warnings anywhere.
- **Fixed a chain-analysis validity bug found during the plan's required
  hand-check:** `station_count > 1` (the original chain definition) is
  inflated by the same downtown buffer overlap already known for density —
  a single location can touch 4 stations without being a chain. Real cost:
  reported 45.7% of locations as chains instead of the true 8.8%. Fixed in
  `step4_rings.py` and `pages/2_Findings.py` to require `location_count >=
  2`. Written up on the methodology page.
- **Observations written up** (below): the aggregate gradient's non-
  monotonicity was traced to a specific, checkable cause — station spacing
  vs. ring radii (Symphony/Westlake 0.268 mi apart, closer than the ring
  system's own reach) — rather than left as an unexplained bump. Also:
  Northgate and UW both have zero businesses in the entire 0-0.1mi ring,
  worth the same attention as the three stations the plan named; UW is the
  sharpest ridership/density outlier (r = 0.684 overall).

### 2026-09-13 — Session 5

- **Ridership reconfigured from one month to twelve.** All twelve months of
  2025 captured as screenshots, collected in a Google Doc (16 stations x 12
  months, PDF export, read via PyMuPDF since Read's PDF path needed
  `poppler`, not installed), transcribed and averaged into
  `avg_monthly_boardings`. Still fully manual — no automation added, just
  more manual reads. `RIDERSHIP_SNAPSHOT` changed from `"May 2025"` to
  `"Jan-Dec 2025 (average of monthly totals)"`.
- **Weekend-inclusive, not weekday-only — and the "redundant column" claim
  was checked, not assumed, and corrected once checked.** Initially assumed
  the dashboard's "average boardings per day" figure was simply
  `total monthly ÷ days in month`. Checked directly against all 192
  station-months: **false** — it matches neither `total ÷ calendar days`
  nor `total ÷ weekdays` (off by roughly +9% and −22% on average
  respectively), so Sound Transit applies some service-day weighting of its
  own; it is a genuinely separate calculation. However, averaged to one
  figure per station across the year, the two metrics correlate at
  **r = 0.998** across all 16 stations (0.998 excluding Stadium too) — for
  the cross-station comparison this project does, close enough to redundant
  that transcribing both would not have changed anything. Not transcribed,
  on that corrected evidence. (The three files that stated the wrong
  "simple derivation" claim before this check — `data/raw/README.md`,
  `pages/3_Methodology.py` — were fixed in this same session.)
- **Found while transcribing: Stadium's April 2025 is a real, large
  outlier** — 193,465 total boardings vs. 21k-95k every other month
  (roughly 3-9x). Very likely a Mariners early-season/home-opener surge
  (Stadium sits at T-Mobile Park/Lumen Field). Kept in the mean like every
  other month — no station gets special-cased — but it pulls Stadium's
  12-month average up substantially above what a "typical" month looks
  like. Worth checking against the Session 6 findings, alongside Rainier
  Beach and SODO (both already flagged with independent explanations).
- `data/raw/ridership_by_station.csv` written: 16 of 16 station names
  matched `stations.csv` exactly on the first try (zero missing, zero
  extra) — no silent join failure.
- Touched: `config.py` (RIDERSHIP_SNAPSHOT), `data/raw/README.md` (schema +
  reasoning, corrected), `PLAN.md` (Session 5 rewritten), `pages/2_Findings.py`
  (chart label), `pages/3_Methodology.py` (temporal-misalignment reframed for
  a year-average; weekday/weekend paragraph corrected with the real numbers).

### 2026-09-13 — Session 4

- Wired the GIS donor join scoped back in Session 1: `step3_geocode.py` now
  joins geometry by City Account Number first (EPSG:2926 -> EPSG:4326,
  90.2% matched), then sends only the unmatched remainder to the Census
  geocoder (94.9% of that remainder). Overall 99.5% geocoded, no bail-out
  needed. Both figures now live in `config.py` (`GEOCODE_*` constants) and
  render on the methodology page — replaced the `[FILL IN]%` placeholder.
- Also resolved a second stale placeholder found in the same file while
  there: "On survival" `[Confirm which applies.]` — already answered in
  Session 1 (active-only, no status column), just never written back.

### 2026-09-13 — Session 3

- Wired the deferred step-2 work: Seattle filter (84,390 -> 58,774), dedupe on
  City Account Number instead of UBI, carried account number + license start
  date through.
- **New methodology structure:** added a "What was filtered out" section that
  renders directly from a new `NAICS_STOREFRONT_EXCLUDE` dict in `config.py` —
  each individually-excluded NAICS code carries its reasoning in one place, so
  the code and the write-up can't drift apart. First entry: `812930` "Parking
  Lots and Garages" (826 rows) excluded — parking is a planned trip decision,
  not the incidental foot traffic this analysis measures. Second entry:
  `812990` "All Other Personal Services" (2,424 rows) — NAICS's residual
  catch-all, sample-characterized as ~90% non-storefront (home-based sole
  proprietors, professional offices, come-to-you services); its ~10%
  plausible-storefront minority is already substantially covered under other
  dedicated codes. Clean dataset now 11,466 rows (was 13,887 before this
  exclusion, 14,728 before any individual exclusions).
- **Reviewed, not excluded:** `459999` "All Other Miscellaneous Retailers"
  (1,190 rows) — same catch-all shape as `812990`, checked the same way,
  opposite result: ~70% plausible storefronts (niche independent shops
  without their own NAICS code), kept. Methodology page now juxtaposes the
  two catch-alls so "checked and fine" is as visible as "checked and
  dropped."

### 2026-09-13 — Session 2

- **Route matching fixed:** `ROUTE_NAME_PATTERN` substring-matched on
  `route_long_name` too, which pulled in the "1 Line Shuttle Bus" replacement
  service alongside the real train. Now an exact match on `route_short_name`.
  Without this, `stations.csv` would have had 17 rows including 3 bus-stop
  duplicates of SODO.
- **GTFS name aliasing added** for two abbreviated stop names ("Univ of
  Washington", "Int'l Dist/Chinatown") so the station-name join key is
  canonical from step 1 onward, not patched later.
- NE 130th/Pinehurst confirmed **not** in this GTFS snapshot — stays out of
  scope for now, 16 stations as planned.

### 2026-09-06 — Session 1

- **Toolchain:** Python 3.12 via `uv`, not 3.11 via pip/conda. System Python is
  3.14 (no geo-stack wheels); the `py` launcher's 3.11 pointed at a deleted
  install. One venv holds both requirement files locally.
- **Business-license data:** split into a CSV spine (canonical, all analyses)
  plus a GIS layer used only to donate point geometry via an account-number
  join. Rejected the GIS layer as primary — it hides a ~10% coverage gap, the
  same bias problem that got OSM rejected.
- **Correction:** "Seattle's business license dataset stops at the city line"
  is not accurate. The CSV carries ~30% non-Seattle rows (licensed here,
  located elsewhere); step 2 filters to `City == "SEATTLE"`. The scope decision
  (Seattle 1 Line only) is unaffected — we still can't get other cities' full
  business populations from this source.
- **COLUMN_MAP** filled in Session 1 rather than Session 3 (the file was
  already in hand).
- **Station coordinates:** `LINKStations.shp` (Sound Transit GIS, in
  `st_gis_shapefiles.zip`) added as a fallback between GTFS parsing and
  hand-building `stations.csv`.

---

## Environment

**Python 3.12.14**, not 3.11 as the plan assumed.
- Why: system Python is 3.14, too new for compiled wheels of the geo stack
  (geopandas/shapely/pyproj/pyogrio). The `py` launcher listed a 3.11 but it
  pointed at a removed install (`Documents\Noble_Desktop\python.exe`).
- 3.12 (a uv-managed CPython build) has wheels for the entire stack and
  installed clean in under a minute. No conda needed.

**Installer: `uv`**, not pip. Same packages, much faster. `.venv` created with
`uv venv --python <3.12 path>`; deps with `uv pip install`.

**One venv holds both requirement files.** `requirements-pipeline.txt` (geo
stack) and `requirements.txt` (streamlit, pandas) are both installed locally.
The lean/heavy split still does its real job — it governs what Streamlit Cloud
installs — but locally a single environment is simpler.

**Versions installed:** geopandas 1.1.4, folium 0.20.0, shapely 2.1.2,
pyproj 3.8.0, streamlit 1.63.0. Reprojection EPSG:4326 -> EPSG:32610 verified
against a known Seattle point.

**Streamlit app:** all four pages (`app.py` + three `pages/`) render their
empty states with no exceptions (checked via `streamlit.testing`).

---

## Data provenance

**Business licenses**
- Downloaded: 2026-09-06
- Source: City of Seattle Open Data — "Active Business License Tax Certificate",
  dataset `wnbq-64tb` (data.seattle.gov). Daily refresh.
- File: `data/raw/business_licenses.csv`
- Row count as downloaded: 84,390 (58,774 with a Seattle address; the rest are
  businesses licensed with Seattle but located in Kent, Bellevue, Tacoma, etc.
  — filtered out in step 2)
- Columns: Business Legal Name, Trade Name, Ownership Type, NAICS Code, NAICS
  Description, License Start Date, Street Address, City, State, Zip, Business
  Phone, City Account Number, UBI
- Status/expiration column present: **no**. This is an active-only snapshot, so
  we can measure **tenure among current licensees** (from License Start Date)
  but **not survival** — closed businesses are absent, not marked. Documented
  limitation.
- Employee count column present: **no**. No business-size proxy available.
- License Start Date: `YYYYMMDD`, 100% parseable, real mass 2018–2026.

**Business license geometry (donor)**
- Downloaded: 2026-09-06
- Source: "Seattle Business License" GIS layer (SeattleCityGIS / ArcGIS Hub;
  catalog stub `wmtg-dzy4` on data.seattle.gov). 54,443 pre-geocoded points,
  `EPSG:2926` (WA State Plane N, feet).
- File: `data/raw/business_licenses_geocoded.geojson`
- Use: **geometry only**. step 3 left-joins these coordinates onto the CSV by
  City Account Number (~53,015 of ~58,774 Seattle rows match), then Census-
  geocodes the remainder. See "Business license source" below for why it is
  not the primary source.

**Ridership**
- Accessed: 2026-09-13. No filters beyond Link / 1 Line and year = 2025
  (evident from the data itself — twelve rows, Jan-Dec 2025, per station).
- Months shown: **Jan-Dec 2025 (all twelve)**, revised from the original
  single-month plan mid-Session-5 — see "Changes" above and
  `data/raw/README.md`.
- Metric: **total boardings per month**, averaged across the twelve months
  into `avg_monthly_boardings`. Deliberately *not* the standard "average
  weekday boardings" — see reasoning below.
- Obtained by: manual screenshots of the Sound Transit dashboard tables (16
  stations x 12 months), collected into a Google Doc by the user, exported
  as PDF, transcribed from there (PyMuPDF rendering, since the standard PDF
  read path needed `poppler`, not installed on this machine). Still fully
  manual — no Power BI automation — just twelve months of manual reading
  instead of one.
- **Metric decision, checked not assumed:** the dashboard tables also show
  an "average boardings per day" figure per month (also weekend-inclusive).
  First assumed to be `total monthly ÷ days in month` and therefore
  redundant with the total - **checked against all 192 station-months and
  that assumption was wrong**: it matches neither `total ÷ calendar days`
  nor `total ÷ weekdays` (off by roughly +9% and −22% on average
  respectively), so Sound Transit applies some service-day weighting of its
  own. It *is* still a defensible thing to skip, but on different grounds:
  averaged to one figure per station across the year, the two metrics
  correlate at **r = 0.998** across all 16 stations — for the cross-station
  comparison this project does, close enough to redundant that transcribing
  both would not have changed the analysis. Not transcribed, on that
  evidence. Full verification script and its output are reproducible from
  the raw 192-row table (kept in this session's scratch files, not the
  repo).
- Using the weekend-inclusive monthly total instead of a weekday-only figure
  is a deliberate choice, not just convenience: weekday ridership is
  disproportionately commute-driven (passing through, not stopping to shop),
  so it would arguably understate pedestrian exposure to the NAICS-filtered
  storefronts this project counts. Cost: not directly comparable to a
  published "average weekday boardings" figure elsewhere. Written up on the
  methodology page under "Ridership as a foot-traffic proxy."
- Averaging twelve months instead of using one (as originally planned)
  smooths seasonality, at the cost of the ridership window possibly spanning
  the Federal Way extension's late-2025 opening internally — also written up
  on the methodology page ("Temporal misalignment").
- **Stadium's April 2025 (193,465 total boardings) is a large, genuine
  outlier** — 3-9x every other month for that station. Very likely a
  Mariners early-season surge (T-Mobile Park/Lumen Field adjacency), not a
  transcription error. Included in the mean like any other month; worth
  checking against the Session 6 ring results.
- Station-name join: **16 of 16 matched `stations.csv` exactly**, zero
  missing, zero extra, on the first attempt.

**GTFS**
- Downloaded: 2026-09-06 (feed dated 2026-08-28 internally)
- Route pattern matched: `route_short_name == "1 Line"` (exact), route_id
  `100479`. Originally substring-matched on both short and long name, which
  also pulled in `1-SHUTTLE` ("1 Line Shuttle Bus" — a bus-bridge replacement
  service) because its route_long_name contains "1 Line" too; that produced 3
  bogus "SODO Busway" bus-stop rows instead of the one real SODO station.
  Fixed to exact match on route_short_name only.
- Two GTFS stop names are abbreviated and were mapped to the canonical names
  used everywhere else: `"Univ of Washington"` -> `"University of
  Washington"`, `"Int'l Dist/Chinatown"` -> `"International
  District/Chinatown"` (`GTFS_NAME_ALIASES` in step 1).
- Stations resolved: 16 of 16, zero unmatched warnings, coordinates spot-
  checked against three known locations (Northgate, Westlake, Rainier Beach)
  and confirmed by the user against a real map for all sixteen.
- Platform-averaging offset measured: 14 m (Capitol Hill) to 72 m (Columbia
  City), mean 48 m from each platform to the averaged station point. Not
  negligible against the innermost 0.1 mi ring (161 m wide). Written up in
  `pages/3_Methodology.py` under "Spatial interpretation".
- NE 130th / Pinehurst included: **no**. Not present anywhere in this feed's
  52 1-Line stops (all cities) — not running as of this snapshot.
- Hand-built instead of joined: no — GTFS join worked once the route filter
  was fixed. Session 2 took well under the 60-minute budget.

---

## Analyst choices

**Business license source: CSV spine + GIS geometry donor**
- Chose: the "Active Business License Tax Certificate" CSV as the canonical
  source for every analysis; the "Seattle Business License" GIS layer used only
  to donate point coordinates (joined on City Account Number).
- Rejected: using the GIS layer as the primary source. It is a strict subset of
  the CSV — it contains only the ~90% of Seattle businesses the City's geocoder
  successfully placed, and silently omits ~5,700 Seattle businesses with no way
  to characterise what is missing. That is the same coverage-bias problem that
  got OpenStreetMap rejected: the gap is not random (new, home-based, informal-
  address businesses) and it correlates with the thing being measured. Starting
  from the CSV and geocoding it ourselves makes every drop visible and
  reportable.
- Rejected: pure CSV with no donor. The account-number join collapses the
  Session 4 geocoding risk — ~53k rows get authoritative City coordinates for
  free, leaving only ~5.7k for the Census geocoder — for no analytical cost.
- Also gained from the CSV: Ownership Type (sole prop / corp / LLC), UBI, split
  address components. Lost vs. GIS: an expiration date (minor — start date
  carries the tenure analysis) and a `BUSINESS_ID` chain link (recoverable via
  the same join if needed).
- Implementation (Session 3/4, not yet wired): step 2 filters to Seattle and
  carries City Account Number + License Start Date; step 3 does the donor join
  before calling Census and reports both match rates.

**NAICS prefixes kept**
- Prefix list unchanged: `44`, `45`, `722`, `812`.
- **Individual exclusion: NAICS `812930` "Parking Lots and Garages" (826
  rows).** Kept by the `812` prefix but excluded on its own. Reasoning
  (also on the methodology page, "What was filtered out" — both read from
  `NAICS_STOREFRONT_EXCLUDE` in `config.py`, one source): paying to park is a
  planned decision made before the trip, not the incidental foot traffic —
  a meal, a purchase — this analysis measures. A commuter who drove and paid
  to park made a different choice than one who walked past a shop from the
  platform; counting both as the same kind of "storefront" would credit
  driving trips to a measure meant to capture walking ones.
- **Individual exclusion: NAICS `812990` "All Other Personal Services"
  (2,424 rows — the single largest category, ~17% of what the prefix filter
  had kept).** This is NAICS's residual catch-all within 812; the
  well-defined personal-service categories (salons, barbers, dry cleaners,
  pet care) already have their own codes and stay in the dataset untouched.
  A hand sample of 40 of the 2,421 category rows: ~10% plausibly walk-in
  storefronts (a dance studio, a massage practice, a dog daycare); the large
  majority were home-based sole proprietors (an individual's name at a
  residential address), professional offices (law/design/consulting/
  investment firms), or services that travel to the customer (hauling,
  pet-sitting, event planning, doula care). Dropped as a category rather
  than triaged row-by-row: no finer NAICS subcode exists to split it, hand-
  reviewing 2,421 rows for ~240 likely storefronts is a poor use of
  remaining hours, and the storefront types in its minority are already
  substantially represented under their own dedicated codes elsewhere — so
  this is a bounded, characterized undercount, not a silent gap.
- **Reviewed and kept: NAICS `459999` "All Other Miscellaneous Retailers"
  (1,190 rows).** Retail's own catch-all, same shape as 812990 above, so
  checked the same way rather than assumed clean. A hand sample of 25 of the
  1,190 rows found the opposite profile: ~70% plausible walk-in storefronts —
  niche independent shops uncommon enough to lack their own NAICS code (a
  violin shop, a comic shop, a record store, a coin shop, a distillery
  tasting room) — against a minority of non-storefront rows (an industrial
  gas supplier, a houseboat-owners' advocacy nonprofit, a couple of
  vague-named LLCs). Kept, unlike 812990: this catch-all's residue is
  dominated by real, if uncommon, retail rather than professional or
  home-based operations. Also on the methodology page, juxtaposed with the
  exclusions — both read from `config.py`
  (`NAICS_STOREFRONT_REVIEWED_KEPT`).
- Effect: NAICS prefix filter 58,774 -> 14,728; parking exclusion
  14,728 -> 13,902; personal-services exclusion 13,902 -> 11,478; final
  clean count after dedup/address validity: **11,466**.

**Ring boundaries**
- Used: 0.1 / 0.2 / 0.3 / 0.6 miles
- Why 0.3 as the walkshed: _[your reasoning]_
- Alternatives tested: _[if any]_

**Overlapping downtown buffers**
- Chose: allow overlap, disclose in methodology
- Rejected: nearest-station assignment, because it understates how many
  stations genuinely serve a downtown block
- Effect: _[how many businesses appear in more than one station's rings]_

**Brand normalization**
- Method: _[exact match after normalization / fuzzy with rapidfuzz]_
- Spot-checked: _[which brands you verified by hand]_
- Known failures: _[names that didn't collapse correctly]_

---

## Quality metrics

- **Geocoding (Session 4, 2026-09-13), two passes:**
  - GIS donor join (City Account Number against
    `business_licenses_geocoded.geojson`, EPSG:2926 -> EPSG:4326): **90.2%**
    (10,345 of 11,466). 1,405 duplicate donor account numbers dropped first
    (exact-coordinate repeats, not distinct locations).
  - Census bulk geocoder, on the 1,121-row remainder only: **94.9%**
    (1,064 of 1,121). Well above the 80% comfort line and the 75% bail-out —
    no `usaddress` parsing needed.
  - **Overall: 99.5%** (11,409 of 11,466). 57 businesses (0.5%) failed both
    passes and are dropped from the geocoded set.
  - Spot-checked 5 points from each source (donor and Census) against
    Google Maps — both look right for their stated address/neighborhood.
  - `geocode_source` column carried into `businesses_geocoded.csv` so the
    two populations stay distinguishable downstream if needed.
- Points dropped by King County bounding-box sanity check: 0 (from either
  source).
- Businesses in final geocoded dataset: **11,409** (of 11,466 cleaned, of
  84,390 originally loaded).
- Stations with no ridership match: **none** — 16 of 16 matched exactly.
- **Rings (Session 6, 2026-09-13):** 6,847 business-ring matches from 11,409
  geocoded businesses across 16 stations x 4 rings. No unmatched-station
  warnings anywhere in the run (stations.csv, businesses_geocoded.csv, and
  ridership_by_station.csv all agree on names).
- **Chain analysis validity bug, caught and fixed (Session 6):** the chain
  metric's `station_count` can be inflated by the same downtown buffer
  overlap already disclosed for density — one physical location inside the
  4-station overlap zone can register as "present at 4 stations" without
  being a chain at all. Verified by hand (the plan's required step):
  PU POWDER and Saigon Drip Kitchen, each with exactly one real location,
  both initially showed up in the "top chains" table. Checked systematically:
  **1,589 of 3,907 normalized brands (41%)** touch >1 station from a single
  location. The bug's real cost: defining "chain" as `station_count > 1`
  (the first version) reported **45.7%** of locations as chains;
  requiring `location_count >= 2` — the only definition consistent with
  what "chain" means — puts the true figure at **8.8%**, a >5x difference.
  Fixed in `src/step4_rings.py` (chain_stats now sorted so real chains float
  to the top; console output explicitly separates "touches >1 station from
  1 location" from genuine multi-location chains) and
  `pages/2_Findings.py` (the `multi = chains[...]` filter now reads
  `location_count > 1`, not `station_count > 1`). Written up on the
  methodology page under "Spatial interpretation," next to the density
  overlap disclosure it's the sibling of.

---

## Observations

**Gradient**
- Not monotonic. Aggregate density by ring: 957 -> 550 -> **592** -> 311
  businesses/sq mi — a real uptick at ring 3 (0.2-0.3mi). Only 2 of 16
  stations decline cleanly (International District/Chinatown, U District).
- **Root cause identified, not just observed:** station spacing vs. ring
  radii. Symphony and Westlake sit 0.268 mi apart — closer than the ring
  system's own reach — so each one's ring 3 partly samples the *other's*
  core, not its own periphery. Both spike at exactly ring 3 (Westlake
  2519->1498->**2570**->781; Symphony 1467->1265->**2410**->779). Beacon
  Hill/Mount Baker sit right at the boundary (0.659 mi) and show only a weak
  version of the same thing — the effect scales with how close the overlap
  is, which is itself evidence it's real and not noise.
- This sharpens the existing "downtown buffers overlap" disclosure into a
  specific causal claim: the *shape* of the aggregate gradient, not just its
  level, is partly a station-spacing artifact.
- One exception the mechanism doesn't explain: Pioneer Square rises from
  ring 1 to ring 2 (797->1520), not ring 2 to ring 3, and its nearest
  neighbor (ID/Chinatown, 0.354 mi) is too far to be the cause. Reads more
  like a genuine siting effect — its commercial core sitting slightly off
  from the platform — left as an open question, not folded into the
  overlap explanation.

**Stations against the pattern**
- **Rainier Beach** (13 businesses within 0.3mi): literal zero in the
  0.2-0.3mi ring specifically, not just low. Consistent with the
  documented "commercial core sits several blocks from the platform."
- **SODO** (110): density *rises* through rings 1-3 (287->308->459) before
  falling. Reads as industrial immediately at the platform, real commerce
  only appearing toward Pioneer Square at the buffer's edge.
- **Stadium** (15): 1 business in ring 1, then 373 in ring 4 — largely
  borrowed from International District/Chinatown, 0.416 mi away and inside
  Stadium's outer ring. Not really "Stadium's own" walkshed.
- **Northgate and University of Washington** — not named in the original
  plan, but the data flags them just as starkly: **zero businesses in the
  entire 0-0.1mi ring**, both of them. Plausibly a still-developing
  redevelopment area (Northgate) and a campus/hospital-immediate platform
  (UW), but not independently confirmed the way the other three were.

**Ridership relationship**
- r = 0.684 (avg monthly boardings vs. businesses within 0.3mi), n=16.
  Moderate-to-strong positive.
- **University of Washington is the sharpest outlier**: lowest commercial
  density of any station (5 businesses within 0.3mi) but 5th-highest
  ridership (152,748/month) — a large positive residual. Consistent with
  the access-mode limitation already on the methodology page: a
  campus/hospital population that rides without shopping nearby.

**Chains**
- After the `location_count >= 2` fix (see "Quality metrics" and "Things
  that went wrong" above for the bug itself): **8.8%** of locations belong
  to a real multi-location chain (153 brands). The pre-fix number would
  have said 45.7% — over 5x too high.
- Real top chains, verified: Subway (7 locations/8 stations), Evergreens
  Salad (7/5), Caffe Ladro (5/5), Westman's Bagels, Metro by T-Mobile,
  Great State Burger, Just Poke, Dough Zone Dumpling House — all real,
  checkable Seattle/PNW brands, not overlap artifacts.
- Whether chain share rises toward the platform (ring 1 vs. ring 4) not yet
  checked — worth doing before the findings write-up.

---

## Things that went wrong

Worth keeping. A limitations section written by someone who hit real
problems reads differently from one assembled from a template.

- **The chain analysis's headline number was wrong by >5x before the
  required hand-check caught it.** `station_count > 1` looked like a
  reasonable definition of "chain" until two single-location businesses
  (PU POWDER, Saigon Drip Kitchen) showed up in the top-15 "most stations"
  table. The downtown buffer overlap — already known and disclosed for
  density — turned out to inflate the chain metric far more severely, in a
  way nothing upstream would have flagged on its own. Full detail under
  "Quality metrics." Lesson: "verify a handful by hand" isn't a formality —
  it's the step that actually catches this class of bug, and a plausible-
  looking top-15 list is not the same as a correct one.
- Earlier in the project: the same lesson showed up with the GTFS route
  match (Session 2) and the "average boardings per day" redundancy claim
  (Session 5) — both were assumed correct until actually checked, and both
  turned out to need correction. Pattern worth remembering for Session 8's
  write-up: check claims against the data before stating them, even ones
  that feel obviously true.

## Open items

Both fixed in step 2, at the source (raw 84,390-row file), rather than
patched on the already-filtered set:

- **Blank `business_name`** — Trade Name empty but Business Legal Name
  populated. Fixed by falling back to Legal Name. Only 2 of these survived
  into the 11,466-row clean set when first spotted, but the fix runs before
  any filtering and caught **22** in the full raw file.
- **`19000101` sentinel `license_start_date`** — a null-date placeholder, not
  a real founding date (would otherwise read as a 126-year-old business).
  Nulled out (set to blank), not dropped — the row itself is fine, just that
  one field. 1 survived into the clean set when first spotted; the fix
  caught **5** in the full raw file.

Verified after re-running step 2: 0 blank `business_name`, 0 `19000101`
values, 1 blank `license_start_date` (the nulled one that happened to survive
filtering) — correctly represented as missing rather than a bogus date. Row
count unchanged at 11,466; these were fixes, not filters.
