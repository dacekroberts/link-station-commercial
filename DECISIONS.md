# Decisions log

Every judgment call, recorded when you make it. The methodology page is
assembled from this file, and reconstructing these choices a week later is
guesswork.

Format: what you chose, why, and what it rules out.

---

## Changes

Macro-level deviations from the original project design, newest first. One line
each; detail lives in the sections below.

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
- Downloaded: _[date]_
- Route pattern matched: _[value of ROUTE_NAME_PATTERN]_
- Stations resolved: _[n]_
- NE 130th / Pinehurst included: _[yes/no, and why]_
- Hand-built instead of joined: _[yes/no]_

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
- Final list: _[...]_
- Why: _[what you saw in the sample of 20 that led here]_
- Considered and rejected: _[e.g. 721 accommodation, 71 arts/rec — why]_
- Effect: _[row count before and after]_

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
