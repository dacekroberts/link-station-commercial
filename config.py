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
# excluded: a cross-station comparison outside Seattle would need each city's
# own business license data, which is out of scope. (The Seattle export does
# list some non-Seattle addresses - those are filtered in step 2 - but it is
# not a source for other cities' business populations.)
#
# Verified against stops.txt in the GTFS feed (Session 2, 2026-09-13,
# feed dated 2026-08-28): all 16 names below matched exactly, zero warnings.
# NE 130th St / Pinehurst was slated to open in 2026 but is NOT in this feed -
# confirmed absent, not included. Re-verify if the GTFS feed is re-downloaded
# later; if it has opened by then, add it between Northgate and Roosevelt and
# note the partial-year caveat. Sound Transit has renamed stations before
# (University Street became Symphony) - re-verify names too on any re-run.
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

# Individual 6-digit NAICS codes excluded from the prefix list above, even
# though their prefix matches. Each entry carries its reasoning so step 2's
# filter and pages/3_Methodology.py's "What was filtered out" section render
# from the same source instead of drifting apart. Add to this dict rather
# than writing prose only on the methodology page.
NAICS_STOREFRONT_EXCLUDE = {
    "812930": (
        "Parking Lots and Garages",
        "Paying to park is a planned decision made before the trip, not the "
        "incidental foot traffic — a meal, a purchase — this analysis is "
        "trying to measure near a platform. Someone who chose to drive and "
        "pay for parking made a different choice than someone who walked "
        "past a restaurant or shop on the way from the platform; treating "
        "the two as the same kind of \"storefront\" would credit driving "
        "trips to a measure meant to capture walking ones.",
    ),
    "812990": (
        "All Other Personal Services",
        "This is NAICS's residual catch-all within 812 — businesses that "
        "didn't fit a more specific personal-services code, which already "
        "exist and are kept separately (nail salons, barber shops, dry "
        "cleaners, pet care each have their own line). A hand sample of 40 "
        "of the 2,421 rows found roughly 10% that plausibly are walk-in "
        "storefronts (a dance studio, a massage therapy practice, a dog "
        "daycare) against a large majority that were home-based sole "
        "proprietors (an individual's name at a residential address), "
        "professional offices (law, design, consulting, investment firms), "
        "or services that travel to the customer rather than the reverse "
        "(hauling, pet-sitting, event planning, doula care). Dropped as a "
        "category rather than triaged row-by-row: no finer NAICS subcode "
        "exists to split it further, manually reviewing 2,421 records for "
        "roughly 240 likely storefronts is a poor use of the project's "
        "remaining hours, and the storefront types this bucket's minority "
        "represents (massage, dance, pet care, wellness) are already "
        "substantially captured under their own dedicated NAICS codes "
        "elsewhere in the dataset — so this is a bounded, characterized "
        "undercount of those categories specifically, not an unaccounted-"
        "for gap.",
    ),
}

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
