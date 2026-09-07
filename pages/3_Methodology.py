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
    LICENSE_SNAPSHOT,
    LICENSE_SOURCE,
    RIDERSHIP_SNAPSHOT,
    RIDERSHIP_SOURCE,
    DOWNTOWN_CLUSTER,
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
(retail, food service, personal services). Addresses geocoded with the
U.S. Census Bureau bulk geocoder; match rate [FILL IN]%.

**Ridership** — {RIDERSHIP_SOURCE}, {RIDERSHIP_SNAPSHOT}, exported by hand
from the published Power BI dashboard.

**Directional ridership** — where used, directional estimates come from
Michael Smith, "Ridership Patterns for Link 1 Line," Seattle Transit Blog,
25 August 2025. The underlying per-direction counts were obtained from
Sound Transit by public records request; the directional split is the
authors' derived estimate, not an agency figure.
"""
)

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
    """
Business license records are a registry of legal entities, not a survey of
storefronts. Home-based sole proprietors and businesses listed at
registered-agent addresses appear identically to physical retail; the NAICS
filter reduces this but does not eliminate it.

Each record is a point, not a footprint. An office tower and a food cart
count as one apiece, so these figures measure establishment counts rather
than commercial floor area.

Geocoding failures are not randomly distributed — addresses with unusual
formatting fail more often, and those may differ systematically from
addresses that match cleanly.

**On survival.** [Confirm which applies.] If this export contains only
currently-active licenses, survival rates cannot be computed: there is no
record of businesses that closed, and therefore no denominator. Tenure
figures in that case describe the distribution among survivors, not
survival itself.
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
Ridership reflects {RIDERSHIP_SNAPSHOT}; business license data reflects
{LICENSE_SNAPSHOT}. The network changed inside that gap. The Federal Way
extension opened in late 2025, and the full East Link extension in 2026
allowed riders travelling between stations north of International
District/Chinatown to take either line — a change expected to reduce 1 Line
counts without any change in underlying travel demand.

Station-level ridership from the earlier period may therefore misstate
current conditions, particularly downtown and at the south end. Figures are
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

Ring boundaries are analyst-chosen. Different cutpoints would produce a
different gradient.

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
