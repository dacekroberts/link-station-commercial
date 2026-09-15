# Commercial density around Seattle's light rail stations

Measures commercial density in concentric rings around the sixteen Link 1
Line stations inside Seattle, tests whether density falls off with distance
from the platform, and looks at which kinds of businesses concentrate
closest.

## Design

Two halves that share nothing but a directory.

The **pipeline** (`src/`) does the geospatial work locally and writes to
`outputs/`. The **app** (`Introduction.py`, `pages/`) reads `outputs/` and
displays it. Nothing else crosses that boundary.

This split is deliberate. Streamlit Cloud installs from `requirements.txt`,
and keeping geopandas out of it avoids the compiled GDAL/GEOS/PROJ
dependencies that are the usual cause of a failed deploy. `outputs/` is
committed to git for the same reason — the app cannot regenerate it.

```
config.py                    every tunable: rings, CRS, station list, NAICS
requirements.txt             app deps only (Streamlit Cloud reads this)
requirements-pipeline.txt    geo stack, local only

src/step1_stations.py        GTFS -> station coordinates
src/step2_clean_businesses.py  license data -> cleaned Seattle addresses
src/step3_geocode.py         GIS geometry join, Census geocoder for the rest
src/step4_rings.py           buffers, spatial join, three analyses
src/step5_map.py             Folium -> outputs/heatmap.html

Introduction.py                        Streamlit entry
pages/1_Heatmap.py                     embeds the saved map
pages/2_Findings_&_EDA.py              gradient, ridership, chains
pages/3_Methodology_&_Limitations.py   sources and limitations

data/raw/                    manual downloads (gitignored, see its README)
data/processed/              intermediate CSVs (gitignored, regenerable)
outputs/                     committed - the app needs these at runtime
```

## Setup

The geo stack needs a Python with compiled wheels available — 3.11 to 3.13
(3.14 was too new as of this writing). This project used `uv` with 3.12:

```bash
uv venv --python 3.12 .venv
uv pip install -r requirements-pipeline.txt   # pipeline
uv pip install -r requirements.txt            # streamlit, to run the app locally
```

Plain `venv` + `pip` works the same way. Activate with
`.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate`
(macOS/Linux). If pip struggles with geopandas,
`conda install -c conda-forge geopandas folium`.

## Running

Fetch the manual downloads first — see `data/raw/README.md`. Then:

```bash
python src/step1_stations.py
python src/step2_clean_businesses.py
python src/step3_geocode.py
python src/step4_rings.py
python src/step5_map.py

streamlit run Introduction.py
```

Each step writes a CSV checkpoint, so a failure costs you one step rather
than the run. Geocoding batches are cached to `data/raw/geocode_cache/` and
skipped on re-run.

## Two things that will bite

**Coordinate systems.** Lat/lon is measured in degrees, and a degree of
longitude is about 75 km at this latitude. Buffering 0.3 miles in degrees
produces ovals of the wrong size. The pipeline projects to EPSG:32610
(metres) before any distance operation and back to EPSG:4326 for display.
If you add spatial code, follow that pattern.

**Station name matching.** The join between ridership and station data is on
name. GTFS names carry suffixes and the dashboard's names may differ. Step 4
prints unmatched stations — do not ignore that warning.

## Scope

Seattle city limits only, Northgate through Rainier Beach. The 1 Line runs
well past both ends and the 2 Line is entirely on the Eastside, but a
cross-station comparison outside Seattle would need each city's own business
license data, and chasing seven more municipal datasets is out of scope here.
(Seattle's export does list some businesses located outside the city — those
are filtered out in step 2.)

Read `pages/3_Methodology_&_Limitations.py` before drawing conclusions from any of this.
