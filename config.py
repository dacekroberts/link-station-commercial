"""Project-wide settings.

Every tunable lives here so the pipeline scripts and the Streamlit app agree
on ring distances, projections, and file locations. Change a value once.
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------

ROOT = Path(__file__).parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

# Pipeline writes to OUTPUTS. The Streamlit app only reads from it.
# Nothing else crosses that boundary.
HEATMAP_HTML = OUTPUTS / "heatmap.html"
STATION_STATS_CSV = OUTPUTS / "station_stats.csv"
RING_STATS_CSV = OUTPUTS / "ring_stats.csv"
CHAIN_STATS_CSV = OUTPUTS / "chain_stats.csv"

STATIONS_CSV = DATA_PROCESSED / "stations.csv"
BUSINESSES_CLEAN_CSV = DATA_PROCESSED / "businesses_clean.csv"
BUSINESSES_GEOCODED_CSV = DATA_PROCESSED / "businesses_geocoded.csv"
RIDERSHIP_CSV = DATA_RAW / "ridership_by_station.csv"

# --- Coordinate reference systems --------------------------------------

# Lat/lon. Degrees. Never buffer in this.
CRS_GEOGRAPHIC = "EPSG:4326"

# UTM zone 10N. Metres. Project to this before any distance operation,
# then project back to CRS_GEOGRAPHIC for Folium.
CRS_PROJECTED = "EPSG:32610"

# --- Ring geometry -----------------------------------------------------

METERS_PER_MILE = 1609.344

# Ring boundaries in miles. Ring i spans RING_EDGES_MILES[i] to [i+1].
# The 0.3 mile mark is the walkshed of interest; 0.3-0.6 is the comparison
# band that gives the gradient something to decline against.
RING_EDGES_MILES = [0.0, 0.1, 0.2, 0.3, 0.6]
RING_EDGES_METERS = [m * METERS_PER_MILE for m in RING_EDGES_MILES]
RING_LABELS = ["0-0.1 mi", "0.1-0.2 mi", "0.2-0.3 mi", "0.3-0.6 mi"]

# --- Station scope -----------------------------------------------------

# 1 Line stations inside Seattle city limits, ordered north to south.
# Stations north of Northgate (Shoreline, Mountlake Terrace, Lynnwood) and
# south of Rainier Beach (Tukwila, SeaTac, Angle Lake, Federal Way) are
# excluded: Seattle's business license dataset stops at the city line.
#
# Verify these names against stops.txt in the GTFS feed. Sound Transit has
# renamed stations before (University Street became Symphony), and NE 130th
# St / Pinehurst was slated to open in 2026 - if it is running, add it
# between Northgate and Roosevelt and note the partial-year caveat.
SEATTLE_1LINE_STATIONS = [
    "Northgate",
    "Roosevelt",
    "U District",
    "University of Washington",
    "Capitol Hill",
    "Westlake",
    "Symphony",
    "Pioneer Square",
    "International District/Chinatown",
    "Stadium",
    "SODO",
    "Beacon Hill",
    "Mount Baker",
    "Columbia City",
    "Othello",
    "Rainier Beach",
]

# Stations whose buffers overlap enough to double-count businesses.
# Flagged for the methodology page, not excluded.
DOWNTOWN_CLUSTER = [
    "Westlake",
    "Symphony",
    "Pioneer Square",
    "International District/Chinatown",
]

# --- Business filtering ------------------------------------------------

# NAICS prefixes kept as storefront commercial. Prefix match on the code
# as a string, so "44" catches 441, 4411, 44111, and so on.
#
# Widening this changes your results materially - it is one of the most
# consequential analyst choices in the project. Whatever you settle on,
# record it in the methodology page.
NAICS_STOREFRONT_PREFIXES = [
    "44",   # Retail trade
    "45",   # Retail trade (continued)
    "722",  # Food services and drinking places
    "812",  # Personal and laundry services
]

# Optional additions worth testing as a sensitivity check:
#   "71"   Arts, entertainment, recreation
#   "721"  Accommodation
#   "621"  Ambulatory health care (clinics, dentists)

# Sanity bounds for geocoder output. Anything outside this is a bad match.
KING_COUNTY_BBOX = {
    "lat_min": 47.15,
    "lat_max": 47.78,
    "lon_min": -122.55,
    "lon_max": -121.05,
}

# --- Provenance --------------------------------------------------------

# These strings are printed on the methodology page. Keep them accurate;
# the temporal gap between them is a documented limitation.
RIDERSHIP_SNAPSHOT = "May 2025"
RIDERSHIP_SOURCE = "Sound Transit System Performance Tracker"
LICENSE_SNAPSHOT = "2026-09-06"
LICENSE_SOURCE = (
    "City of Seattle Open Data - Active Business License Tax Certificate "
    "(dataset wnbq-64tb). Point geometry joined from the companion GIS layer "
    "'Seattle Business License' where account numbers match."
)
