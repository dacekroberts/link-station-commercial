# Decisions log

Every judgment call, recorded when you make it. The methodology page is
assembled from this file, and reconstructing these choices a week later is
guesswork.

Format: what you chose, why, and what it rules out.

---

## Changes

Macro-level deviations from the original project design, newest first. One line
each; detail lives in the sections below.

### 2026-09-13 — Session 3 (in progress)

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
- Accessed: _[date]_
- Month shown: _[e.g. May 2026]_
- Dashboard filters set: _[line, metric, any others]_
- Obtained by: _[dashboard export / manual transcription]_

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

- Geocoder match rate: _[%]_
- Points dropped by bounding box: _[n]_
- Businesses in final dataset: _[n]_
- Stations with no ridership match: _[list, or none]_

---

## Observations

Write these down in session 6, while the numbers are in front of you.

**Gradient**
- _[monotonic? how steep? which rings?]_

**Stations against the pattern**
- _[which, and your explanation]_

**Ridership relationship**
- _[correlation, and what the access-mode problem does to its meaning]_

**Chains**
- _[share of locations, whether it rises toward the platform]_

---

## Things that went wrong

Worth keeping. A limitations section written by someone who hit real
problems reads differently from one assembled from a template.

- _[...]_

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
