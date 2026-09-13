"""Methodology and limitations.

Grouped by which claim each limitation constrains, rather than as a flat
list. The three that matter most are access mode, the temporal gap, and
station siting - if you trim, trim elsewhere.

Placeholders in [brackets] need your actual numbers before this is done.
"""

import streamlit as st

from config import (
    RING_EDGES_MILES,
    NAICS_STOREFRONT_PREFIXES,
    NAICS_STOREFRONT_EXCLUDE,
    NAICS_STOREFRONT_REVIEWED_KEPT,
    LICENSE_SNAPSHOT,
    LICENSE_SOURCE,
    RIDERSHIP_SNAPSHOT,
    RIDERSHIP_SOURCE,
    DOWNTOWN_CLUSTER,
    GEOCODE_DONOR_MATCHED,
    GEOCODE_CENSUS_MATCHED,
    GEOCODE_CENSUS_REMAINDER,
    GEOCODE_DONOR_RATE,
    GEOCODE_CENSUS_RATE,
    GEOCODE_OVERALL_RATE,
    GEOCODE_TOTAL,
    GEOCODE_TOTAL_FAILED,
    GEOCODE_FAILED_RATE,
)

st.set_page_config(page_title="Methodology", page_icon="📋", layout="wide")

st.title("Methodology and limitations")

st.header("Data sources")

st.markdown(
    f"""
**Station locations** — GTFS feed from Sound Transit's Open Transit Data
downloads. Station coordinates come from `stops.txt`, filtered to 1 Line
stops within Seattle city limits. Platforms sharing a station name are
averaged to a single point.

**Commercial spaces** — {LICENSE_SOURCE}, downloaded {LICENSE_SNAPSHOT}.
Filtered to NAICS prefixes {', '.join(NAICS_STOREFRONT_PREFIXES)}
(retail, food service, personal services). Addresses geocoded in two passes:
a join against the City's own GIS geometry by account number matched
{GEOCODE_DONOR_RATE:.1%} of businesses ({GEOCODE_DONOR_MATCHED:,} of
{GEOCODE_DONOR_MATCHED + GEOCODE_CENSUS_REMAINDER:,}) directly; the
remaining {GEOCODE_CENSUS_REMAINDER:,} went to the U.S. Census Bureau bulk
geocoder, which matched {GEOCODE_CENSUS_RATE:.1%} of those
({GEOCODE_CENSUS_MATCHED:,} of {GEOCODE_CENSUS_REMAINDER:,}). Overall:
{GEOCODE_OVERALL_RATE:.1%} of businesses geocoded.

**Ridership** — {RIDERSHIP_SOURCE}, {RIDERSHIP_SNAPSHOT}, exported by hand
from the published Power BI dashboard.

**Directional ridership** — where used, directional estimates come from
Michael Smith, "Ridership Patterns for Link 1 Line," Seattle Transit Blog,
25 August 2025. The underlying per-direction counts were obtained from
Sound Transit by public records request; the directional split is the
authors' derived estimate, not an agency figure.
"""
)

st.header("What was filtered out")

st.markdown(
    """
The NAICS prefix filter above is broad by design — it is meant to catch
retail, food service, and personal services in one pass, not to hand-pick
categories. That breadth pulls in a few things that don't belong for
specific reasons, including a couple of NAICS "catch-all" codes (labelled
"All Other...") broad enough that they needed a closer look before deciding
either way. Rather than narrow the prefix list itself — and lose categories
it correctly keeps — individual NAICS codes are excluded one at a time, each
with its reasoning recorded here so the choice is checkable rather than
silent.
"""
)

if NAICS_STOREFRONT_EXCLUDE:
    for code, (label, reason) in NAICS_STOREFRONT_EXCLUDE.items():
        st.markdown(f"**Excluded — {label}** (NAICS `{code}`)")
        st.markdown(reason)
else:
    st.markdown("*No categories excluded yet.*")

if NAICS_STOREFRONT_REVIEWED_KEPT:
    st.markdown(
        "**Reviewed the same way, kept.** Not every catch-all code turned "
        "out to be a problem — one looked identical in shape to the "
        "exclusions above and was checked anyway, precisely so \"we looked "
        "and it's fine\" is recorded as deliberately as \"we looked and "
        "dropped it,\" rather than the category just quietly staying in."
    )
    for code, (label, reason) in NAICS_STOREFRONT_REVIEWED_KEPT.items():
        st.markdown(f"**Kept — {label}** (NAICS `{code}`)")
        st.markdown(reason)

st.header("Method")

st.markdown(
    f"""
Station points are projected from EPSG:4326 to EPSG:32610 (UTM zone 10N)
so that distances are measured in metres, then buffered into concentric
annuli at {', '.join(str(e) for e in RING_EDGES_MILES[1:])} miles. Each ring
subtracts the disc inside it, so a business falls in exactly one ring per
station. Businesses are assigned by spatial join, and counts are normalised
by ring area to give density per square mile.
"""
)

st.header("Limitations")

st.subheader("What \"commercial space\" means here")

st.markdown(
    f"""
Business license records are a registry of legal entities, not a survey of
storefronts. Home-based sole proprietors and businesses listed at
registered-agent addresses appear identically to physical retail; the NAICS
filter reduces this but does not eliminate it.

Each record is a point, not a footprint. An office tower and a food cart
count as one apiece, so these figures measure establishment counts rather
than commercial floor area.

Geocoding failures are not randomly distributed — addresses with unusual
formatting fail more often, and those may differ systematically from
addresses that match cleanly. Two sources are stacked here: a business
missing from the GIS donor layer isn't necessarily a hard address — it may
simply postdate that snapshot, or not have carried over for an unrelated
reason — but the City's layer only includes businesses it successfully
geocoded, so donor-absence could also skew toward the same hard-to-place
addresses Census then struggles with. The {GEOCODE_TOTAL_FAILED} businesses
({GEOCODE_FAILED_RATE:.1%}) that failed both passes are too few to
characterise confidently, but are unlikely to be a random sample of the
whole.

**On survival.** This export contains only currently-active licenses — there
is no status or expiration column, confirmed by inspection (Session 1).
Survival rates cannot be computed: there is no record of businesses that
closed, and therefore no denominator. Tenure figures describe the
distribution among survivors, not survival itself.
"""
)

st.subheader("Ridership as a foot-traffic proxy")

st.markdown(
    """
Counts derive from Automatic Passenger Counters on the trains, which
register door passages rather than unique riders. Transfers are counted more
than once.

Boardings measure departures, not arrivals. For a customer-arrival proxy
alightings are conceptually closer, though at most stations the two are
similar over a full day since riders make round trips.

**The boardings figure used here includes weekends**, deliberately, not by
default. It is each station's average monthly total (twelve months of 2025,
averaged), not the "average weekday boardings" figure transit agencies more
commonly report. That choice cuts both ways: weekday ridership is
disproportionately commute-driven — passing through on the way to a job, not
stopping to shop — so a weekday-only figure would arguably *understate*
pedestrian exposure to the storefronts this analysis counts. Including
weekends better matches the discretionary, retail-adjacent trips this
project cares about, at the cost of not being directly comparable to
published "average weekday boardings" figures elsewhere. A same-shaped
"average daily boardings" figure also appears on Sound Transit's dashboard
(also weekend-inclusive) but was not transcribed. It is not a simple
derivation of the monthly total — checked directly against all 192
station-months, it matches neither `total ÷ calendar days` nor
`total ÷ weekdays` (off by roughly +9% and −22% respectively, on average),
so Sound Transit is applying some service-day weighting of its own. What
was checked instead: averaged to one figure per station across 2025, the
two metrics correlate at **r = 0.998** across the sixteen stations. For a
cross-station comparison, which is what this analysis does, that is close
enough to redundant that transcribing both would not have changed anything
— confirmed empirically, not assumed.

**Access mode is the substantive problem.** A large share of riders at some
stations arrive by car or connecting bus and board directly. Sound Transit's
garage at Lynnwood City Center accounts for roughly 40% of that station's
riders, and much of Northgate's ridership transfers in from the adjacent
transit center. Those passengers never pass a storefront. Ridership
therefore overstates pedestrian exposure at park-and-ride and transfer-heavy
stations and understates it at walk-up stations.

**On directional figures.** Sound Transit's raw per-direction data has no
expansion method applied and does not reconcile with published totals.
Seattle Transit Blog found the discrepancy large enough to conclude the file
captures only a subset of trips, and used it for directional ratios while
taking absolute counts from the official dashboard. This project follows the
same convention.
"""
)

st.subheader("Temporal misalignment")

st.markdown(
    f"""
Ridership reflects {RIDERSHIP_SNAPSHOT}; business license data reflects a
single snapshot on {LICENSE_SNAPSHOT}. Two gaps follow from that, not one.

First, the twelve months averaged into the ridership figure are not
evenly comparable to each other: the Federal Way extension opened in late
2025, so the ridership window itself may span a system change rather than
sit entirely before or after one. Averaging smooths month-to-month noise,
but it can also blend two different network configurations into one number.

Second, the license snapshot postdates the full ridership window by roughly
nine months, and the full East Link extension completed in 2026 — entirely
after the ridership period this analysis uses — allowing riders travelling
between stations north of International District/Chinatown to take either
line. That's expected to reduce 1 Line counts without any change in
underlying travel demand.

Station-level ridership from 2025 may therefore misstate current (2026)
conditions, particularly downtown and at the south end. Figures are
labelled with their snapshot date wherever they appear.
"""
)

st.subheader("Spatial interpretation")

st.markdown(
    f"""
Buffers are straight-line radii, not walksheds. Seattle's terrain makes this
consequential: I-5, the Montlake Cut, and steep grades near Beacon Hill and
Rainier Beach put part of each circle out of walking reach. Reported density
is therefore lower than the density a pedestrian actually encounters.

Buffers around {', '.join(DOWNTOWN_CLUSTER)} overlap. Businesses in the
overlap are counted for each station, inflating downtown density relative to
isolated stations. This is disclosed rather than corrected: assigning each
business to its nearest station would understate how many stations genuinely
serve a downtown block.

**That same overlap distorts the chain analysis more severely, and was
corrected there rather than merely disclosed.** A single physical location
inside the four-station overlap can touch multiple stations on its own —
verified by hand: a one-location shop with no other branches showed up
"present at 4 stations," indistinguishable from a real chain. Checked
across every normalized brand, **1,589 of 3,907 (41%)** touch more than one
station from exactly one physical location. Defining "chain" as
`station_count > 1` — the first version of this analysis — would have
reported **45.7%** of locations as chains; correctly requiring 2+ real
locations puts the true figure at **8.8%**. The chain statistics used
throughout this project require `location_count >= 2`, never station
count alone.

Ring boundaries are analyst-chosen. Different cutpoints would produce a
different gradient.

**Station points are an average of two platforms, not a single focal point.**
Northbound and southbound platforms are recorded separately in the GTFS feed
and collapsed to one coordinate per station. The offset between a platform
and that averaged point ranges from 14 m (Capitol Hill) to 72 m (Columbia
City) across the sixteen stations, averaging 48 m. Against the innermost
ring's 161 m width (0.1 mile), that is not negligible: a business near the
inner-ring boundary could fall in a different ring depending on whether the
averaged point or a single platform is used as the reference. It matters less
for the outer rings — 48 m against a 483 m radius (0.3 mile) is a small
fraction — so the effect is concentrated in the finest-grained comparison.

**Station siting is not random.** Link was routed through corridors that
were already commercially active, so proximity and density are partly
co-determined. Rainier Beach shows the reverse case: the neighbourhood's
commercial centre sits several blocks from the platform, so the buffer
captures less activity than the neighbourhood contains.
"""
)

st.subheader("Inference")

st.markdown(
    """
With sixteen stations, cross-station comparisons rest on few observations.
Ring-level analysis expands this to roughly sixty station-ring units, but
rings within a station are not independent of each other.

No non-transit control corridor is included, so there is no baseline for
what commercial density would look like absent a station.

Findings here are associations. Nothing in this analysis identifies a causal
effect of transit access on business location.
"""
)

st.header("What a fuller version would add")

st.markdown(
    """
- **Control corridors.** Ballard and Fremont are commercially dense with no
  light rail, and would give the gradient something to be compared against.
- **The 2 Line.** Entirely outside Seattle city limits, so it would require
  business license data from Bellevue and Redmond.
- **A before-and-after design.** Northgate, Roosevelt and U District opened
  in October 2021. License issue dates would support comparing business
  formation on either side of that opening — the strongest available version
  of this analysis, and the one that comes closest to a causal claim.
"""
)
