# Decisions log

Every judgment call, recorded when you make it. The methodology page is
assembled from this file, and reconstructing these choices a week later is
guesswork.

Format: what you chose, why, and what it rules out.

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
- Downloaded: _[date]_
- Source: _[exact dataset name and URL]_
- Row count as downloaded: _[n]_
- Status/expiration column present: _[yes/no — determines whether survival
  is computable or only tenure among survivors]_
- Employee count column present: _[yes/no]_

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
