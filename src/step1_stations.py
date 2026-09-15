"""Step 1 - Station coordinates from the Sound Transit GTFS feed.

Input:  data/raw/gtfs.zip  (download from Sound Transit's Open Transit Data page)
Output: data/processed/stations.csv

GTFS spreads what you need across four tables. Link stations are not
labelled as such anywhere - you find them by walking the relationships:

    routes.txt     find the 1 Line's route_id
      -> trips.txt      find trip_ids on that route
      -> stop_times.txt find stop_ids served by those trips
      -> stops.txt      get the name and lat/lon for those stops

The feed also carries buses, Sounder, and the streetcar, so skipping the
join and grepping stops.txt for likely names will pull in bus stops.

BUDGET NOTE: give this one hour. If routes.txt does not look the way you
expect, or the join returns nothing sensible, stop and hand-build the CSV
instead - there are only sixteen stations and the schema is four columns.
A hand-built file is completely defensible; note it in the methodology.

Run:  python src/step1_stations.py
"""

import sys
import zipfile

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from config import DATA_RAW, STATIONS_CSV, SEATTLE_1LINE_STATIONS  # noqa: E402

GTFS_ZIP = DATA_RAW / "gtfs.zip"

# Adjust after inspecting routes.txt. Sound Transit's naming has changed
# over the years, so do not trust this constant without looking.
ROUTE_NAME_PATTERN = "1 Line"

# GTFS abbreviates two station names in stop_name. Map them to the canonical
# names used everywhere else (config.py, the ridership CSV you'll type in
# Session 5) so the join key is consistent from here on - do not carry GTFS's
# abbreviations forward.
GTFS_NAME_ALIASES = {
    "Univ of Washington": "University of Washington",
    "Int'l Dist/Chinatown": "International District/Chinatown",
}


def load_gtfs_table(zip_path, filename):
    """Read one .txt table out of a GTFS zip into a DataFrame."""
    with zipfile.ZipFile(zip_path) as z:
        with z.open(filename) as f:
            return pd.read_csv(f, dtype=str)


def main():
    if not GTFS_ZIP.exists():
        sys.exit(
            f"No GTFS feed at {GTFS_ZIP}.\n"
            "Download it from Sound Transit's Open Transit Data downloads page "
            "and save it there. See data/raw/README.md."
        )

    routes = load_gtfs_table(GTFS_ZIP, "routes.txt")

    # LOOK AT THIS BEFORE GOING FURTHER. The column that holds "1 Line"
    # may be route_short_name or route_long_name depending on the feed.
    print("Routes in this feed:")
    print(routes[["route_id", "route_short_name", "route_long_name"]].to_string())
    print()

    # Match route_short_name EXACTLY, not a substring search across both name
    # columns. This feed also has a "1 Line Shuttle Bus" replacement service
    # (route_id "1-SHUTTLE") whose route_long_name contains "1 Line" too - a
    # substring match on route_long_name pulls in its street-level bus stops
    # alongside the real train stations. We want only the train.
    link_routes = routes[routes["route_short_name"].fillna("") == ROUTE_NAME_PATTERN]
    if link_routes.empty:
        sys.exit(
            f"No route matched {ROUTE_NAME_PATTERN!r}. Check the printout above "
            "and update ROUTE_NAME_PATTERN."
        )
    print(f"Matched route_ids: {list(link_routes['route_id'])}\n")

    trips = load_gtfs_table(GTFS_ZIP, "trips.txt")
    stop_times = load_gtfs_table(GTFS_ZIP, "stop_times.txt")
    stops = load_gtfs_table(GTFS_ZIP, "stops.txt")

    link_trips = trips[trips["route_id"].isin(link_routes["route_id"])]
    link_stop_ids = stop_times[
        stop_times["trip_id"].isin(link_trips["trip_id"])
    ]["stop_id"].unique()

    link_stops = stops[stops["stop_id"].isin(link_stop_ids)].copy()
    link_stops["stop_lat"] = link_stops["stop_lat"].astype(float)
    link_stops["stop_lon"] = link_stops["stop_lon"].astype(float)
    link_stops["stop_name"] = link_stops["stop_name"].replace(GTFS_NAME_ALIASES)

    print(f"Found {len(link_stops)} stops on the 1 Line (all cities):")
    print(link_stops["stop_name"].to_string())
    print()

    # Filter to Seattle. GTFS has no city field, so this matches against the
    # curated list in config.py. Fuzzy because feed names carry suffixes like
    # "Northgate Station" or directional markers.
    def matches_seattle(stop_name):
        return any(
            s.lower() in stop_name.lower() or stop_name.lower() in s.lower()
            for s in SEATTLE_1LINE_STATIONS
        )

    seattle = link_stops[link_stops["stop_name"].apply(matches_seattle)].copy()

    # Platforms often appear as separate stops sharing a name. Collapse to
    # one row per station by averaging. Measured offset from platform to
    # averaged point: 14-72 m across the 16 stations (mean 48 m) - a small
    # fraction of the 0.3 mile ring radius (483 m) but a meaningful fraction
    # of the innermost 0.1 mile ring width (161 m). See
    # pages/3_Methodology_&_Limitations.py "Spatial interpretation" for the
    # write-up.
    stations = (
        seattle.groupby("stop_name", as_index=False)
        .agg(latitude=("stop_lat", "mean"), longitude=("stop_lon", "mean"))
        .rename(columns={"stop_name": "station"})
    )

    print(f"Kept {len(stations)} Seattle stations (expected ~16):")
    print(stations.to_string(index=False))

    missing = [
        s for s in SEATTLE_1LINE_STATIONS
        if not any(s.lower() in n.lower() or n.lower() in s.lower()
                   for n in stations["station"])
    ]
    if missing:
        print(f"\nWARNING - expected but not matched: {missing}")
        print("Either the feed names them differently or they are not yet open.")

    STATIONS_CSV.parent.mkdir(parents=True, exist_ok=True)
    stations.to_csv(STATIONS_CSV, index=False)
    print(f"\nWrote {STATIONS_CSV}")


if __name__ == "__main__":
    main()
