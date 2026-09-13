# Manual data acquisition

Three files must be downloaded by hand. Nothing in `src/` will run without
them. This is the work that cannot be handed to an agent.

---

## 1. `gtfs.zip` — station coordinates

Sound Transit's Open Transit Data downloads page publishes the regional GTFS
feed. Download it and save it here, unchanged, as `gtfs.zip`.

Used by: `src/step1_stations.py`

---

## 2. `business_licenses.csv` — commercial spaces

City of Seattle Open Data portal, **"Active Business License Tax Certificate"**
(dataset `wnbq-64tb`). Export as CSV, save here as `business_licenses.csv`.

Inspected 2026-09-06 (see `DECISIONS.md` for the full record):

- Columns: Business Legal Name, Trade Name, Ownership Type, NAICS Code, NAICS
  Description, License Start Date, Street Address, City, State, Zip, Business
  Phone, City Account Number, UBI. `COLUMN_MAP` in step 2 is filled from these.
- **No status or expiration column** — active-only snapshot. Tenure among
  current licensees is computable; survival is not. Documented as a limitation.
- **No employee-count column.**
- ~30% of rows have a non-Seattle address (licensed here, located elsewhere).
  Step 2 filters to `City == "SEATTLE"`.

Record the download date in `config.py` under `LICENSE_SNAPSHOT`.

Used by: `src/step2_clean_businesses.py`

---

## 2b. `business_licenses_geocoded.geojson` — geometry donor

ArcGIS Hub, **"Seattle Business License"** (SeattleCityGIS; catalog stub
`wmtg-dzy4`). Download the GeoJSON, save here under this name.

This is the same businesses as file 2, pre-geocoded by the City. Step 3 joins
its coordinates onto the CSV by City Account Number so that only the unmatched
remainder goes to the Census geocoder. It is **not** the primary source — it
silently omits ~10% of Seattle businesses (see `DECISIONS.md`).

Used by: `src/step3_geocode.py`

---

## 2c. `st_gis_shapefiles.zip` — Link station points (optional, Session 2)

Sound Transit public GIS data (`STPublicData.zip`). Contains `LINKStations.shp`,
an authoritative point layer of Link stations. If parsing station coordinates
out of the GTFS feed (step 1) proves fiddly, this shapefile is a clean
fallback — no route-pattern matching needed. Save the zip here under this name.

Used by: `src/step1_stations.py` (fallback path)

---

## 3. `ridership_by_station.csv` — station boardings

From Sound Transit's System Performance Tracker ridership dashboard.

The dashboard is an embedded Power BI report. Its data is not in the page
HTML and there is no CSV endpoint behind it, so this project reads the
numbers by hand rather than automating the extraction — do not automate
this: browser automation against a Power BI embed is roughly three hours of
work with a real chance of failure, for data needed once.

**What was actually done (Session 5):** rather than one month, all twelve
months of 2025 were captured by hand as screenshots (total boardings per
month, per station), collected into a Google Doc and transcribed from there.
Averaging a full year smooths out any single month's seasonality — more
robust than the single-month figure the schema below originally assumed.

The dashboard's tables also show an "average boardings per day" figure per
month (also weekend-inclusive, so not the industry-standard *weekday*
figure either). It was checked, not just assumed, before deciding to skip
it: month by month it is *not* a simple derivation of the total — it
matches neither `total ÷ calendar days` nor `total ÷ weekdays` (off by
roughly +9% and −22% on average across all 192 station-months), so Sound
Transit applies some service-day weighting of its own. But averaged to one
figure per station across the year, the two metrics correlate at
**r = 0.998** across all sixteen stations — close enough to redundant for a
cross-station comparison that transcribing both would not have changed
anything. Not transcribed, on that evidence.

**Schema** — station names must match `data/processed/stations.csv` exactly,
or the join in step 4 silently drops rows. One row per station, holding the
average of its twelve monthly totals:

```csv
station,avg_monthly_boardings
Northgate,124000
Roosevelt,98000
...
```

Record the month(s) covered, and any filters set on the dashboard, in
`config.py` under `RIDERSHIP_SNAPSHOT`. Note the access date here too — that's what makes
the step reproducible.

Used by: `src/step4_rings.py`

---

## Optional: directional boardings and alightings

Seattle Transit Blog published a small CSV of May 2025 1 Line boarding and
alighting counts, obtained from Sound Transit via public records request,
linked from the methodology comment on this post:

https://seattletransitblog.com/2025/08/25/ridership-patterns-for-link-1-line/

**Read the caveat before using it.** Sound Transit staff noted the raw
directional data has no expansion method applied, and the blog's authors
concluded from the mismatch with published totals that the file captures only
a subset of trips. Use it for the ratio between directions. Take absolute
counts from the dashboard.
