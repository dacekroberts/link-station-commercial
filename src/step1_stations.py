"""Step 1: station coordinates from the Sound Transit GTFS feed.

Input:  data/raw/gtfs.zip (Sound Transit's Open Transit Data page)
Output: data/processed/stations.csv

GTFS doesn't label Link stations. They're found by joining four tables:

    routes.txt          the 1 Line's route_id
      -> trips.txt      the trips on that route
      -> stop_times.txt the stops those trips serve
      -> stops.txt      each stop's name and coordinates

Matching names in stops.txt directly would also catch bus stops, since the
feed covers every mode.

Run:  python src/step1_stations.py
"""

import sys
import zipfile

import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from config import DATA_RAW, STATIONS_CSV, SEATTLE_1LINE_STATIONS  # noqa: E402

GTFS_ZIP = DATA_RAW / "gtfs.zip"

# Matched exactly against route_short_name. Sound Transit's route naming
# has changed over the years; re-check routes.txt when the feed is updated.
ROUTE_NAME_PATTERN = "1 Line"

# GTFS abbreviates two station names in stop_name. Mapped here to the
# canonical names used everywhere else (config.py, the ridership CSV):
# station name is the join key between ridership and stations, so GTFS's
# abbreviations must not be carried forward.
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

    # Printed for inspection: the column holding "1 Line" can be
    # route_short_name or route_long_name depending on the feed.
    print("Routes in this feed:")
    print(routes[["route_id", "route_short_name", "route_long_name"]].to_string())
    print()

    # Exact match on route_short_name, not a substring search across both
    # name columns. The feed also has a "1 Line Shuttle Bus" replacement
    # service (route_id "1-SHUTTLE") whose route_long_name contains "1 Line";
    # a substring match would pull in its street-level bus stops.
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
    # curated list in config.py, loosely, because feed names carry suffixes
    # like "Northgate Station" or directional markers.
    def matches_seattle(stop_name):
        return any(
            s.lower() in stop_name.lower() or stop_name.lower() in s.lower()
            for s in SEATTLE_1LINE_STATIONS
        )

    seattle = link_stops[link_stops["stop_name"].apply(matches_seattle)].copy()

    # Platforms often appear as separate stops sharing a name; averaging
    # collapses them to one row per station. Platform-to-average offset is
    # 14-72 m across the 16 stations (mean 48 m): small against the 0.3 mile
    # ring radius (483 m), meaningful against the innermost 0.1 mile ring
    # width (161 m). See "Spatial interpretation" in
    # pages/3_Methodology_&_Limitations.py.
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
