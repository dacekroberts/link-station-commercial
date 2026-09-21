"""Methodology and limitations.

Grouped by which claim each limitation constrains, rather than as a flat
list. The three that matter most are access mode, the temporal gap, and
station siting - if you trim, trim elsewhere.

Placeholders in [brackets] need your actual numbers before this is done.
"""

import streamlit as st

from components import (
    render_sidebar_nav_label,
    render_social_links,
    set_base_font,
    set_sidebar_width,
)
from config import (
    RING_EDGES_MILES,
    NAICS_STOREFRONT_PREFIXES,
    NAICS_STOREFRONT_EXCLUDE,
    NAICS_STOREFRONT_REVIEWED_KEPT,
    CHAIN_ANALYSIS_EXCLUDE_BRANDS,
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

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_social_links()

st.title("Methodology")

st.subheader("Method")

st.markdown(
    f"""
Station coordinates come out of the GTFS feed as latitude/longitude in
EPSG:4326, the standard coordinate system GPS data uses, measured in
degrees. To measure distance in meters instead of degrees, I project
those points to EPSG:32610 (UTM zone 10N), a coordinate system built for
this part of the Pacific Northwest that measures in meters instead.

Then I buffer each station into four concentric rings at
{', '.join(str(e) for e in RING_EDGES_MILES[1:])} miles. Each ring
subtracts the disc inside it, so a business only falls into one ring per
station, never double-counted at the same station. Businesses get
assigned through a spatial join, and I normalize the raw counts by ring
area to get a density figure (businesses per square mile) instead of a
raw count that would just reward a bigger ring.

These four distances weren't picked at random. The rings are meant to
capture a rider's spontaneous walkable detour off their trip, not just
physical nearness to the platform. A business sitting at the outer edge
of ring 4 could still see foot traffic from people walking to or from
work or home, but that's a commute passing by, not a station-driven
impulse stop, so I'd expect its benefit from the station specifically to
have already dropped off compared to the inner rings.

Rather than assuming it, I checked the 0.6 mile outer edge against real
walking-trip data. Using the distance-decay parameters Yang and Diez-Roux
(2012) fit to 2009 National Household Travel Survey data, roughly 77% of
one-way walking trips for meals and 72% for shopping (the closest matches
to my food-service and retail categories) land at 0.6 miles or less.

Recreation, the longest-distance purpose in that study, is the outlier at
only about 50% within 0.6 miles, which is the pattern I needed to see,
not a convenient coincidence of picking a lenient category on purpose.
This is general U.S. walking behavior, though, not a study of Seattle
transit riders specifically, so it supports my ring choice rather than
proving it outright.

The Yang and Diez-Roux study is part of the reason I used four tiers instead of one
flat cutoff. It found that 65% of U.S. walking trips exceed the 0.25-mile
distance conventionally assumed as the max in transportation planning,
which argues against relying on a single threshold at all. One ring
alone would have collapsed whatever structure actually exists between
the platform and the outer edge into a single undifferentiated number,
instead of letting a gradient, or a departure from one, actually show up
in the data.
"""
)

st.subheader("Data Sources")

st.markdown(
    f"""
Station locations come from Sound Transit's Open Transit Data GTFS feed.
I pulled station coordinates from `stops.txt`, filtered down to 1 Line
stops within Seattle city limits, and averaged platforms that share a
station name into a single point.

Commercial spaces come from {LICENSE_SOURCE}; downloaded {LICENSE_SNAPSHOT}.
I filtered to NAICS prefixes {', '.join(NAICS_STOREFRONT_PREFIXES)} to
capture retail, food service, and personal services. Addresses were
geocoded in two passes: a join against the City's own GIS geometry by
account number matched {GEOCODE_DONOR_RATE:.1%} of businesses
({GEOCODE_DONOR_MATCHED:,} of {GEOCODE_DONOR_MATCHED + GEOCODE_CENSUS_REMAINDER:,})
directly, and the remaining {GEOCODE_CENSUS_REMAINDER:,} went through the
U.S. Census Bureau's bulk geocoder, which matched {GEOCODE_CENSUS_RATE:.1%}
of those ({GEOCODE_CENSUS_MATCHED:,} of {GEOCODE_CENSUS_REMAINDER:,}).
Overall, {GEOCODE_OVERALL_RATE:.1%} of businesses got geocoded.

Ridership numbers come from {RIDERSHIP_SOURCE}, {RIDERSHIP_SNAPSHOT},
exported by hand from the published Power BI dashboard.
"""
)

st.subheader("What Was Filtered Out")

st.markdown(
    """
I kept the NAICS prefix filter above broad on purpose. It's meant to
catch retail, food service, and personal services in one pass rather
than hand-picking categories one at a time. That breadth pulls in a few
things that don't really belong, including a couple of NAICS
"catch-all" codes (labeled "All Other...") that were broad enough to
need a closer look before I could decide either way. Instead of
narrowing the prefix list itself, which would risk losing categories it
correctly keeps, I excluded individual NAICS codes one at a time, with
my reasoning recorded here so the choice is checkable instead of silent.
"""
)

if NAICS_STOREFRONT_EXCLUDE:
    for code, (label, reason) in NAICS_STOREFRONT_EXCLUDE.items():
        st.markdown(f"**Excluded: {label}** (NAICS `{code}`)")
        st.markdown(reason)
else:
    st.markdown("*No categories excluded yet.*")

if NAICS_STOREFRONT_REVIEWED_KEPT:
    for code, (label, reason) in NAICS_STOREFRONT_REVIEWED_KEPT.items():
        st.markdown(f"**Kept: {label}** (NAICS `{code}`)")
        st.markdown(reason)

if CHAIN_ANALYSIS_EXCLUDE_BRANDS:
    for brand, (label, reason) in CHAIN_ANALYSIS_EXCLUDE_BRANDS.items():
        st.markdown(f"**Excluded from chain analysis: {label}**")
        st.markdown(reason)

    st.markdown(
        "These are real "
        "businesses, and nothing about how I filtered, geocoded, or "
        "counted them was wrong; they still count fully toward the "
        "density, gradient, and ridership figures everywhere else on "
        "this site. They only became a problem for one specific piece "
        "of analysis, which brands cluster near stations, and for a "
        "reason that has nothing to do with transit."
    )
    st.markdown(
        "Each one is a corporate food-service **contractor** (NAICS "
        "`722310`, \"Food Service Contractors\"), not an independent "
        "chain. One vendor running cafeterias inside however many "
        "buildings its client company occupies looks identical, in a "
        "brand-name count, to a coffee chain that made eight separate "
        "real-estate decisions to be near a platform, but it isn't the "
        "same kind of \"chain.\""
    )
    st.markdown(
        "Averaging it in would credit one company's office-campus "
        "footprint as evidence about transit-adjacency site selection. "
        "This is a limitation of the approach rather than an error in "
        "it: name-based brand grouping can't tell \"repeated deliberate "
        "choice\" apart from \"one vendor, many kitchens\" on its own."
    )

st.subheader("Citations")

st.markdown(
    """
A few claims on this page lean on outside research, not just this
project's own data. They're cited here in full, and referenced by
author and year wherever they're used above. Not every source below is
cited inline yet. One is background reading that shaped how I think
about the subject, kept on record for a future write-up rather than
backing a specific claim today.
"""
)

st.markdown(
    "Merilus, Jean-Yves. \"10: Urbanization.\" *Cultural Geography "
    "(C-ID GEOG 120)*, LibreTexts, "
    "socialsci.libretexts.org/Courses/Coalinga_College/Cultural_Geography__"
    "(C-ID_GEOG_120)/10:_Urbanization/. Accessed 14 Sept. 2026."
)

st.markdown(
    "Yang, Yong, and Ana V. Diez-Roux. \"Walking Distance by Trip Purpose "
    "and Population Subgroups.\" *American Journal of Preventive Medicine*, "
    "vol. 43, no. 1, 2012, pp. 11-19."
)

st.subheader("AI Use")

st.markdown(
    """
This project is based in HTML & Python and was built in tandem with Claude Code. Before starting, I
completed five Skilljar courses on Claude Code over about a month,
building real working knowledge of it rather than just enough to copy
and paste.

From there, Claude Code helped me write and debug pipeline scripts,
build the Streamlit pages you're looking at, and catch bugs I would
have otherwise missed. The analysis itself, every interpretation and
judgment call, is mine.
"""
)

st.divider()

st.markdown(
    '<h1 style="font-size:44px; font-weight:700; line-height:52.8px; '
    'margin:0 0 0.5rem 0;">Limitations</h1>',
    unsafe_allow_html=True,
)

st.subheader("What \"commercial space\" means here")

st.markdown(
    f"""
Business license records are a registry of legal entities, not a survey
of storefronts. Home-based sole proprietors and businesses listed at
registered-agent addresses show up identically to physical retail in
this data. The NAICS filter reduces that problem, but it doesn't
eliminate it.

Each record is a point, not a footprint. An office tower and a food cart
both count as one apiece, so these figures are measuring establishment
counts, not commercial floor area.

Geocoding failures aren't randomly distributed. Addresses with unusual
formatting fail more often, and those addresses might differ
systematically from the ones that match cleanly. Two sources stack on
top of each other here: a business missing from the GIS donor layer
isn't necessarily a hard address to place; it could just postdate that
snapshot or not have carried over for some unrelated reason, but the
City's layer only includes businesses it successfully geocoded in the
first place, so donor-absence could still skew toward the same
hard-to-place addresses that then trip up Census too.

The {GEOCODE_TOTAL_FAILED} businesses ({GEOCODE_FAILED_RATE:.1%}) that
failed both passes are too small a group to characterize with any
confidence, but I doubt they're a random sample of the whole.

**On survival.** This export only contains currently active licenses.
There's no status or expiration column, which I confirmed by inspection
back in Session 1. That means survival rates can't be computed at all,
since there's no record of businesses that closed and therefore no
denominator to work with. The tenure figures on this site describe the
distribution among survivors, not survival itself.
"""
)

st.subheader("Am I publishing people's names at their homes?")

st.markdown(
    """
The heatmap plots each business as a pin carrying its name at a geocoded
address, and as above, this registry lists home-based sole proprietors
alongside physical storefronts. A trade name someone chose for their shop
is commercial information, and mapping it is the entire point of this
project. A registrant's own name at what is really their house is not,
even though the registry holding it is public: a registry entry sits
behind a search box, while a map pin is a plotted coordinate. So I
checked which of the two I was about to publish, before publishing it.

Two things could put a person's name on this map. The first is the
fallback in step 2 that fills a blank trade name from the legal business
name; that fires on 22 of the 84,390 raw rows, and none of those 22 reach
the map. The second is a sole proprietor with no trade name at all, who
gets published under whatever the registry holds. I can identify that
case exactly rather than guess at it, because the registry carries both
names: if someone chose a trade name, the two strings differ. Requiring
that the published name *be* the legal entity name, and that the entity
be a sole proprietorship rather than a company, narrows 4,120 pins to 41,
and to 12 once I keep only residentially zoned addresses (using the
City's published land use zoning layer). That is few enough to read
rather than sample, and reading them, seven are genuinely someone's name
and five are trade names that happen to match the legal one. **Seven
pins, 0.17% of the map, three of them on single-family land.**

Those seven names are not published. The map withholds a pin's name
wherever it is the registrant's own identity by the test above, showing
*Name withheld (sole proprietor)* in its place; the pin, its location,
its category and its ring all stay, so no figure anywhere on this site
changes. That covers 41 pins rather than seven, because the rule
deliberately over-reaches: around three dozen of them are trade names
that happen to match the legal name, and they lose their label too. I
preferred that to a hand-written list of the seven, which would go stale
against a newer license export without ever saying so. Excluding NAICS
`812990` above had already removed the category where home-based sole
proprietors concentrate, which is most of why the number was small to
begin with. The check itself
can be re-run after any change to filtering, and it prints numbers rather
than a verdict. Its limits are worth stating plainly: matching a name
against the legal entity name can't tell a real shop trading under its
owner's name from a registrant sitting at home, zoning describes
permitted use rather than actual use, no individual record here was
verified, and nobody was contacted. Checked 2026-09-20.
"""
)

st.subheader("Ridership as a foot-traffic proxy")

st.markdown(
    """
Counts come from Automatic Passenger Counters on the trains, which
register door passages rather than unique riders, so transfers get
counted more than once.

Boardings measure departures, not arrivals. Alightings would be
conceptually closer to a customer-arrival proxy, though at most stations
the two end up similar over a full day since most riders make round
trips anyway.

**The boardings figure I use here includes weekends on purpose**, not by
default. It's each station's average monthly total across all twelve
months of 2025, not the "average weekday boardings" figure transit
agencies more commonly report. That choice cuts both ways. Weekday
ridership is disproportionately commute-driven, people passing through
on the way to a job rather than stopping to shop, so a weekday-only
figure would arguably understate pedestrian exposure to the storefronts
I'm counting here.

Including weekends better matches the discretionary, retail-adjacent
trips this project actually cares about, at the cost of not being
directly comparable to the "average weekday boardings" figures published
elsewhere. Sound Transit's own dashboard shows a similarly shaped
"average daily boardings" figure (also weekend-inclusive), but I didn't
transcribe it.

It isn't a simple derivation of the monthly total either; checked
directly against all 192 station-months, it matches neither
`total ÷ calendar days` nor `total ÷ weekdays` (off by roughly +9% and
-22% respectively, on average), so Sound Transit is applying some
service-day weighting of its own. What I did check: averaged to one
figure per station across 2025, the two metrics correlate at
**r = 0.998** across the sixteen stations. For a cross-station
comparison, which is what this analysis does, that's close enough to
redundant that transcribing both wouldn't have changed anything. I
confirmed that empirically rather than just assuming it.

**Access mode is the bigger problem.** A large share of riders at some
stations arrive by car or a connecting bus and board directly, never
passing a storefront. Much of Northgate's ridership, for example,
transfers in from the adjacent transit center. So ridership overstates
pedestrian exposure at park-and-ride and transfer-heavy stations, and
understates it at walk-up stations.

**On directional figures.** Sound Transit's raw per-direction data has
no expansion method applied to it and doesn't reconcile with the
published totals. Seattle Transit Blog found the discrepancy large
enough to conclude the file only captures a subset of trips, and used it
for directional ratios while pulling absolute counts from the official
dashboard instead. I followed the same convention here.
"""
)

st.subheader("Temporal misalignment")

st.markdown(
    f"""
Ridership reflects {RIDERSHIP_SNAPSHOT}, and business license data
reflects a single snapshot from {LICENSE_SNAPSHOT}. That mismatch
creates two separate gaps, not just one.

First, the twelve months I averaged into the ridership figure aren't
evenly comparable to each other. The Federal Way extension opened in
late 2025, so the ridership window itself might span a system change
instead of sitting entirely before or after one. Averaging smooths out
month-to-month noise, but it can also blend two different network
configurations into a single number without showing that it did.

Second, the license snapshot comes roughly nine months after the
ridership window ends, and the full East Link extension finished in
2026, entirely after the ridership period I'm using here. That
extension lets riders traveling between stations north of International
District/Chinatown take either line now, which I'd expect to reduce 1
Line ridership counts without any real change in underlying travel demand.

Station-level ridership from 2025 could therefore misstate current, 2026
conditions, especially downtown and at the south end. I've labeled
figures with their snapshot date wherever they appear on this site.
"""
)

st.subheader("Spatial interpretation")

st.markdown(
    f"""
My buffers are straight-line radii, not actual walksheds, and Seattle's
terrain makes that a real problem here. I-5, the Montlake Cut, and the
steep grades near Beacon Hill and Rainier Beach all put part of each
circle out of walking reach. That means the density figures I report are
lower than the density a pedestrian would actually encounter on foot.
This isn't just an issue with my own data either; it's a recognized gap
in the transportation-research literature. Yang and Diez-Roux (2012)
note that most travel datasets only record trip start and end points,
not the route someone actually walked, and that street-network distance
is the more accurate alternative to straight-line distance, just rarely
available.

Buffers around {', '.join(DOWNTOWN_CLUSTER)} overlap each other. A
business sitting in that overlap gets counted for every station whose
buffer reaches it, which inflates downtown density relative to more
isolated stations. I'm disclosing this rather than correcting it,
because assigning each business to only its nearest station would
understate how many stations genuinely serve a downtown block. This
isn't a marginal effect either: of the businesses that fall within any
station's ring at all, **1,767 (42.9%)** are claimed by more than one
station's ring set. That's computed directly from the spatial join,
not estimated.

**That same overlap distorts the chain analysis even more severely, and
I corrected it there instead of just disclosing it.** A single physical
location inside the four-station overlap can touch multiple stations
all on its own. I verified this by hand: a one-location shop with no
other branches showed up as "present at 4 stations," indistinguishable
from an actual chain.

Checking across every normalized brand, **1,589 of 3,900 (40.7%)** touch
more than one station from exactly one physical location. Defining
"chain" as `station_count > 1`, which is what the first version of this
analysis did, would have reported **45.5%** of locations as chains.
Correctly requiring 2+ real locations instead puts the true figure at
**8.5% (152 brands)**. Every chain statistic used throughout this
project requires `location_count >= 2`, never station count alone.

**Brand matching in this project is exact, not fuzzy**, which is a real
limitation of this kind of approach generally, not just something
specific to my project. Name normalization catches most chains, but
formatting variants like spacing or punctuation on the same brand can
still land on two different keys unless I catch them by hand. That
happened here with "Rudy's Barbershop" and "Molly Moon's Homemade Ice
Cream," which I patched with a small known-case lookup rather than a
general fix. So the chain-share figures on this site are a **lower
bound**, not an exact count. A fuzzy-matching pass, using something like
`rapidfuzz`, could close some of that gap, but at the cost of needing
every match checked by hand afterward.

Ring boundaries are choices I made as the analyst. Different cutpoints
would produce a different gradient.

**Station points here are an average of two platforms, not a single
focal point.** Northbound and southbound platforms get recorded
separately in the GTFS feed, and I collapsed them to one coordinate per
station. The offset between an individual platform and that averaged
point ranges from 14 m (Capitol Hill) to 72 m (Columbia City) across the
sixteen stations, averaging 48 m.

Against the innermost ring's 161 m width (0.1 mile), that's not a
negligible difference: a business sitting near the inner-ring boundary
could fall in a different ring depending on whether I used the averaged
point or a single platform as the reference. It matters a lot less for
the outer rings, since 48 m against a 483 m radius (0.3 mile) is a much
smaller fraction, so this effect is concentrated in the finest-grained
comparison.

**Station siting isn't random either.** The link rail was routed through
corridors that were already commercially active, so proximity and
density are partly co-determined here rather than one simply causing the
other. Rainier Beach shows the reverse case: the neighborhood's
commercial center actually sits several blocks away from the platform,
so my buffer captures less activity than the neighborhood really
contains.
"""
)

st.subheader("Inference")

st.markdown(
    """
With only sixteen stations, cross-station comparisons rest on a pretty
small number of observations. Ring-level analysis expands that to
roughly sixty station-ring units, but rings within the same station
aren't independent of each other, so it isn't really sixty separate data
points either.

I didn't include a non-transit control corridor, so there's no baseline
showing what commercial density would look like without a station there
at all.

The findings on this site are associations, not causes. Nothing in this
analysis identifies a causal effect of transit access on where
businesses choose to locate.
"""
)

st.header("What a Fuller Version Would Add")

st.markdown(
    """
- **Control corridors.** Ballard and Fremont are both commercially dense
  with no light rail at all, and would give the gradient something real
  to be compared against.
- **The 2 Line.** It's entirely outside Seattle city limits, so covering
  it would require pulling business license data from Bellevue and
  Redmond too.
- **A before-and-after design.** Northgate, Roosevelt, and U District all
  opened in October 2021. License issue dates would let me compare
  business formation on either side of that opening, which would be the
  strongest available version of this analysis and the one that comes
  closest to an actual causal claim.
- **Continuous distance-decay weighting instead of flat rings.** My
  current four annuli treat every business within a band identically,
  regardless of how close it actually sits to the boundary. A negative
  exponential decay function, `P(d) = e^(-βd)`, the same form Yang and
  Diez-Roux (2012) fit to national walking-trip data and that Zhao et al.
  (2003) apply directly to transit walk accessibility as an alternative
  to flat buffers, would model pedestrian attenuation continuously
  instead of as four discrete steps. That's real added complexity this
  project's scope didn't call for, though.
"""
)
