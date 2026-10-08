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
CHAIN_RING_STATS_CSV = OUTPUTS / "chain_ring_stats.csv"
CITYWIDE_COVERAGE_CSV = OUTPUTS / "citywide_coverage.csv"

STATIONS_CSV = DATA_PROCESSED / "stations.csv"
BUSINESSES_CLEAN_CSV = DATA_PROCESSED / "businesses_clean.csv"
BUSINESSES_GEOCODED_CSV = DATA_PROCESSED / "businesses_geocoded.csv"
RIDERSHIP_CSV = DATA_RAW / "ridership_by_station.csv"

# --- Coordinate reference systems --------------------------------------

# Lat/lon. Degrees. Never buffer in this.
CRS_GEOGRAPHIC = "EPSG:4326"

# UTM zone 10N. Meters. Project to this before any distance operation,
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
# excluded: comparing them would need each city's own business license
# data, which is out of scope. (The Seattle export lists some non-Seattle
# addresses; step 2 filters them out. It is not a source for other cities.)
#
# All 16 names match stops.txt exactly in the GTFS feed dated 2026-08-28.
# Pinehurst (NE 130th St) opened 2026-09-30, after that feed, so it is not
# in it. On a newer download, add it north of Northgate with a
# partial-year caveat. Sound Transit renames stations
# (University Street became Symphony), so re-check the names too.
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
# One of the most consequential analyst choices in the project: widening
# it changes results materially. Record any change on the methodology page.
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

# 6-digit NAICS codes excluded even though their prefix matches. Each entry
# carries its reasoning, so step 2's filter and the methodology page's
# "What was filtered out" section render from one source and can't drift.
# Add exclusions here, not as prose on the methodology page alone.
NAICS_STOREFRONT_EXCLUDE = {
    "812930": (
        "Parking Lots and Garages",
        "Paying to park is a planned decision made before the trip, not "
        "incidental foot traffic. A meal or a shopping purchase is more in "
        "line with what this analysis is trying to measure near a "
        "platform. Someone who chose to drive and "
        "pay for parking made a different choice than someone who walked "
        "past a restaurant or shop on the way from the platform; treating "
        "the two as the same kind of \"storefront\" would credit driving "
        "trips to a measure meant to capture walking ones.",
    ),
    "812990": (
        "All Other Personal Services",
        "This is NAICS's residual catch-all within 812. Businesses that "
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
        "elsewhere in the dataset. This is a bounded, characterized "
        "undercount of those categories specifically, not an unaccounted-"
        "for gap.",
    ),
}

# Catch-all NAICS codes reviewed like the exclusions above (the prefix
# match sweeps in a large, undifferentiated bucket) but kept after a hand
# sample showed a different profile. Rendered beside NAICS_STOREFRONT_EXCLUDE
# on the methodology page, so "checked and fine" is as visible a decision
# as "checked and dropped."
NAICS_STOREFRONT_REVIEWED_KEPT = {
    "459999": (
        "All Other Miscellaneous Retailers",
        "Retail's own catch-all, structurally identical in shape to 812990 "
        "above, but a hand sample of 25 of the 1,190 rows found the "
        "opposite profile. Roughly 70% were plausible walk-in storefronts: "
        "niche independent shops uncommon enough that they don't have their "
        "own NAICS code (a violin shop, a comic shop, a record store, a "
        "coin shop, a distillery tasting room), against a minority of "
        "non-storefront rows (an industrial gas supplier, a houseboat-"
        "owners' advocacy nonprofit, a couple of vaguely named LLCs). Kept: "
        "unlike the personal-services catch-all, this bucket's residue is "
        "dominated by real, if uncommon, retail rather than professional or "
        "home-based operations.",
    ),
}

# Excluded from the brand/chain grouping only. These are real, correctly
# geocoded and counted businesses, and they still count fully toward the
# density, gradient, and ridership analyses (step4_rings.py's
# ring_stats/station_stats). Each is a corporate food-service CONTRACTOR:
# one vendor running cafeterias in its client's office buildings, not an
# independent chain repeatedly choosing transit-adjacent sites.
#
# The filter is these three brand names, not a NAICS code. NAICS 722310
# (Food Service Contractors) identified them and is disclosed on the
# methodology page, but it tags only 1 of Compass One's 24 records (the
# other 23 are 722514, "Cafeterias, Grill Buffets, and Buffets"), and 722514
# would also catch ~30 genuine independent cafes (Boon Boona Coffee, Turtle
# Coffee, Tea Addicts, and others).
CHAIN_ANALYSIS_EXCLUDE_BRANDS = {
    "COMPASS ONE": (
        "Compass One LLC",
        "23 of its 24 licensed locations use NAICS 722514, not 722310, "
        "but all 24 cluster in South Lake Union under addresses that read "
        "as office-campus buildings (Terry Ave N, Boren Ave N, Fairview "
        "Ave N), not walk-in storefronts. Compass Group is a real, large "
        "contract food-service company; \"11 locations\" in the raw chain "
        "count reflected one vendor's footprint across a single client's "
        "campus, not 11 independent site-selection decisions.",
    ),
    "BON APPETIT MANAGEMENT": (
        "Bon Appétit Management Company",
        "NAICS 722310 (Food Service Contractors) throughout; another "
        "national contract caterer, same pattern as Compass One at a "
        "smaller scale in this dataset (4 locations).",
    ),
    "FLIK INTERNATIONAL": (
        "Flik International",
        "NAICS 722310 (Food Service Contractors) throughout; a third "
        "national contract caterer (3 locations), same pattern.",
    ),
}

# Sanity bounds for geocoder output. Anything outside this is a bad match.
KING_COUNTY_BBOX = {
    "lat_min": 47.15,
    "lat_max": 47.78,
    "lon_min": -122.55,
    "lon_max": -121.05,
}

# --- Geocoding results (2026-09-13) ------------------------------------
# Recorded by hand, not computed at runtime: the app reads only outputs/,
# and the source (data/processed/businesses_geocoded.csv) is local-only and
# gitignored. Re-run step3_geocode.py and update these by hand if the source
# data changes. Full detail in docs/DECISIONS.md.
GEOCODE_DONOR_MATCHED = 10345
GEOCODE_CENSUS_MATCHED = 1064
GEOCODE_TOTAL = 11466
GEOCODE_DONOR_RATE = GEOCODE_DONOR_MATCHED / GEOCODE_TOTAL
GEOCODE_CENSUS_REMAINDER = GEOCODE_TOTAL - GEOCODE_DONOR_MATCHED
GEOCODE_CENSUS_RATE = GEOCODE_CENSUS_MATCHED / GEOCODE_CENSUS_REMAINDER
GEOCODE_OVERALL_RATE = (GEOCODE_DONOR_MATCHED + GEOCODE_CENSUS_MATCHED) / GEOCODE_TOTAL
GEOCODE_TOTAL_FAILED = GEOCODE_TOTAL - GEOCODE_DONOR_MATCHED - GEOCODE_CENSUS_MATCHED
GEOCODE_FAILED_RATE = GEOCODE_TOTAL_FAILED / GEOCODE_TOTAL

# --- Provenance --------------------------------------------------------

# Printed on the methodology page. Keep them accurate; the temporal gap
# between them is a documented limitation.
#
# Ridership covers all twelve months of 2025, transcribed by hand:
# avg_monthly_boardings in ridership_by_station.csv is the average of each
# station's twelve monthly totals, not a single-month snapshot. See
# data/raw/README.md and docs/DECISIONS.md.
RIDERSHIP_SNAPSHOT = "Jan-Dec 2025 (average of monthly totals)"
RIDERSHIP_SOURCE = "Sound Transit System Performance Tracker"
LICENSE_SNAPSHOT = "2026-09-06"
LICENSE_SOURCE = (
    "City of Seattle Open Data - Active Business License Tax Certificate "
    "(dataset wnbq-64tb). Point geometry joined from the companion GIS layer "
    "'Seattle Business License' where account numbers match"
)

# --- Authorship marks ----------------------------------------------------
# Invisible marks in the rendered map and pages that tie a copy back to this
# project: `lsc:v1:<id>:<check>`, where the check is an HMAC of the id under
# a secret key kept outside the repository. Only the checks are committed
# (FINGERPRINT_TABLE), so rendering never needs the key. Metadata only: no
# coordinate, count, name or visible text changes. scripts/fingerprint.py
# writes the table and verifies copies; see its docstring.
FINGERPRINT_PREFIX = "lsc:v1"
FINGERPRINT_TABLE = ROOT / "fingerprint_marks.json"
_fingerprint_cache = {}


def fingerprint_mark(ident):
    """`lsc:v1:<ident>:<check>` from the committed table, or None when the
    table has no entry. A missing or unreadable table never breaks a render;
    `python scripts/fingerprint.py coverage` is what catches it."""
    import json
    if not _fingerprint_cache:
        try:
            _fingerprint_cache.update(json.loads(FINGERPRINT_TABLE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            return None
    check = _fingerprint_cache.get(ident)
    return f"{FINGERPRINT_PREFIX}:{ident}:{check}" if check else None
