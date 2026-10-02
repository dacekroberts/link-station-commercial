"""Streamlit entry point.

Reads only from outputs/. Never runs the pipeline - that keeps the deployed
app free of the compiled geospatial stack, which is the usual reason a
Streamlit Cloud deploy fails.

Run:  streamlit run "Overview_&_Introduction.py"
"""

import pandas as pd
import streamlit as st

from components import (
    render_sidebar_nav_label,
    render_social_links,
    render_train_banner,
    set_base_font,
    set_sidebar_width,
)
from config import (
    STATION_STATS_CSV,
    CITYWIDE_COVERAGE_CSV,
    LICENSE_SNAPSHOT,
    RIDERSHIP_SNAPSHOT,
)

st.set_page_config(
    page_title="Transit and commercial density in Seattle",
    page_icon="🚈",
    layout="wide",
)

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_train_banner("overview")
render_social_links()

st.title("Commercial Density Around Seattle's Light Rail Stations")
st.caption("By Dace Roberts")

st.subheader("Overview")

# Skimmable orientation before the denser prose: three short lists, not
# paragraphs. The container key adds an "st-key-overview_columns" class so
# the divider CSS targets only these columns, not the metrics row below.
with st.container(key="overview_columns"):
    st.markdown(
        """
        <style>
        .st-key-overview_columns [data-testid="stHorizontalBlock"]
        > [data-testid="stColumn"]:not(:first-child) {
            border-left: 1px solid rgba(128, 128, 128, 0.3);
            padding-left: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    provides_col, workflow_col, takeaways_col = st.columns(3)
    with provides_col:
        st.markdown("**What This Analysis Provides**")
        st.markdown(
            "- This project measures business counts near transit stations "
            "to analyze significance\n"
            "- Core component: interactive heatmap allowing customizable "
            "visualizations of the database\n"
            "- Findings, methodology, and flowchart pages contribute to "
            "meaningful insights, validity of the database, and "
            "informative infrastructure"
        )
    with workflow_col:
        st.markdown("**Project Workflow**")
        st.markdown(
            "- Heatmapped database compiles NAICS business data and GIS "
            "locational data\n"
            "- Findings and EDA are tied directly to the heatmapped "
            "database\n"
            "- Findings do not imply causality, only possible correlations"
        )
    with takeaways_col:
        st.markdown("**Key Takeaways**")
        st.markdown(
            "- Business density and chain share both peak closest to "
            "transit platforms\n"
            "- Ridership volume per station shares a moderate correlation "
            "with the number of businesses nearby\n"
            "- More than a third of Seattle's storefront businesses lie "
            "within the transit corridor"
        )

st.divider()

st.subheader("Introduction")

st.markdown(
    """
This project centers on a concentric-ring analysis of commercial density
around the City of Seattle's Link light rail 1 line service area,
covering all 16 stations within official Seattle city limits.
Business-license data, sourced directly from the City of Seattle's own
published open data, forms the commercial backbone of the analysis,
categorized by NAICS code. Additionally, ridership data per station is
included as a proxy for foot traffic levels around each station to
provide insights on potential commercial value. Lastly, chain analysis
was done to determine the level of chain presence within transit hub
localities. Concentric ring analysis has been visually published as a
dynamic heatmap viewable on the corresponding page. Resulting findings &
EDA, as well as methodology & limitations, are similarly featured on
their own pages. Further analysis of 1-line stations outside of Seattle
city limits or the newer 2 line are not included at this time as an
appropriate scope limitation, though I am not discounting their addition
at a future time.
"""
)

if STATION_STATS_CSV.exists():
    stats = pd.read_csv(STATION_STATS_CSV)
    # [1, 2, 1], not st.columns(3): the middle metric's label clips with an
    # ellipsis in equal thirds at the 1280px test width.
    # The 30px font applies to the last column ("Data Retrieved on") only.
    # That column is 206.8px wide; a date like "2026-09-06" needs 212px at
    # 36px and 177px at 30px. Re-measure if a label, the date format, or the
    # base font changes.
    st.markdown(
        """
        <style>
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child
        [data-testid="stMetricValue"] { font-size: 30px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    left, mid, right = st.columns([1, 2, 1])
    left.metric("Number of Stations Analyzed", len(stats))
    if CITYWIDE_COVERAGE_CSV.exists():
        coverage = pd.read_csv(CITYWIDE_COVERAGE_CSV).iloc[0]
        in_rings = int(coverage["businesses_in_rings"])
        citywide = int(coverage["businesses_citywide"])
        # Whole number as the metric value; fraction and percentage go in a
        # caption. "4,120 / 11,409 (36.1%)" as the value overflowed the
        # column and truncated with an ellipsis. The full string stays in
        # the DOM, so check this visually, not with a text-content check.
        mid.metric("Businesses within concentric ring area of Link stations", f"{in_rings:,}")
        mid.caption(f"of {citywide:,} citywide ({in_rings / citywide:.1%})")
    else:
        mid.metric("Businesses within concentric ring area of Link stations", "N/A")
    right.metric("Data Retrieved on", LICENSE_SNAPSHOT)
    # States both dates outright: no metric above shows a ridership figure,
    # so a caption referring to "the two dates" would have nothing to point at.
    st.caption(
        f"Business data was retrieved {LICENSE_SNAPSHOT}. Ridership figures "
        f"reflect {RIDERSHIP_SNAPSHOT}."
    )
else:
    st.info(
        "No results yet. Run the pipeline to generate them:\n\n"
        "```\n"
        "python src/step1_stations.py\n"
        "python src/step2_clean_businesses.py\n"
        "python src/step3_geocode.py\n"
        "python src/step4_rings.py\n"
        "python src/step5_map.py\n"
        "```"
    )

st.divider()
st.subheader("What I Asked")
# Pairs with "What I Found" directly below. The three numbered questions
# are the Findings page's section hypotheses, worded identically there;
# a change to one needs the same change in the other.
st.caption(
    "These are the questions I started with: one larger question, and "
    "three narrower ones this project could actually test. The headline "
    "answers follow directly below."
)
st.markdown(
    "Do transit platforms bring businesses into their neighborhoods, or do "
    "cities place transit along preexisting commercial corridors?"
)
st.markdown(
    """
1. **Concentric ring gradient.** Does commercial density drop off with
   decreased proximity to transit hubs?
2. **Ridership.** Does station boarding volume track commercial density?
3. **Chains.** Do multi-location brands appear at more stations than
   independents? In the middle of my chain share investigation, the
   driving question shifted to more closely mirror the gradient's: Does
   chain share rise as you approach transit platforms?
"""
)
st.markdown(
    """
The 1 Line's route offers some context for the larger question above.
Much of the clustering near its stations likely predates the rail
itself, as the line largely ran through developed neighborhoods like downtown and Capitol Hill that already had
commercial cores, rather than seeding new ones. Newer stations tell a
different story: University of Washington, added in 2016, sits at the
center of campus and hospital land rather than an established retail core
the line reached. This project measures the resulting density pattern,
not which came first at each station.
"""
)

st.divider()
st.subheader("What I Found")
st.caption(
    "These are the headline numbers. For the full breakdown, including "
    "per-station detail, the correlation's leverage check, and further "
    "pattern discovery, see the Findings & EDA page."
)
st.markdown(
    """
- **Density falls off fast, but not cleanly.** Businesses per square mile
  drop 62.9% between the innermost and outermost rings, 837 to 310, with
  a slight uptick at the third ring. It's small, but it traces back to a
  specific, checkable cause rather than just being noise.
- **Ridership and density move together, moderately.** The correlation
  across all sixteen stations lands at r = 0.684, strong enough to
  matter, not strong enough to lean on by itself.
- **Businesses cluster far less evenly than ridership does.** Businesses'
  spread across stations is about 1.8 times as uneven as ridership's,
  proportionally, not just in raw numbers.
- **Chains lean into platform proximity too.** Chain share is highest
  right at the platform, 9.5% in the first ring, and falls to 6.8% by the
  fourth, the same declining pattern found in overall density.
"""
)

st.divider()
st.subheader("Why Seattle?")

st.markdown(
    """
Seattle has several factors that make it an intriguing option to
explore this particular topic within. Firstly, the unparalleled growth
of the city, centered around its burgeoning tech sector, has created a
slew of both exciting opportunities and concerns about existing
infrastructure's capacity for growth accommodation. Those concerns lean
into the second factor, which is a severe lack of centralized public
transit removed from privatized commuting costs. Before 2009, Seattle's
public transit was largely constrained to bus systems serving the wider
area, with only a select few downtown attractions housing fully integrated
transit networks. With buses as the legacy primary option for public
transit, the negative externalities of increased urban density on
transportation have uniformly affected all residents, whether or not they
own their own vehicle. Buses get stuck in traffic just as much as a
private vehicle, save for bus-only lanes, which are not prevalent enough
to fully circumvent the high-density downsides. The end result is city
residents being stuck in a lose-lose situation: Either you brave the
traffic and put up with vehicle ownership, or you budget an increased
share of time to afford walking to bus stops from your residence, waiting
for the bus, and dealing with the traffic's impacts regardless.

As a result, the introduction of the Link rail to the city's transit
infrastructure (first opened in 2009 and significantly expanded this
decade) has begun to change that equation. Starting with the subject of
this paper, the 1 Line serves the main network servicing the primary
north-south urban corridor. At the time of writing, the city has already
expanded into a 2nd line that serves an east-west area connecting the
greater King County's east side to the city of Seattle itself, suggesting
the local government is keen on furthering the reach and utility of the
Link rail. This firm stance should indicate to business owners that
support for the Link rail, including attempts to increase ridership and
accessibility, is only set to continue on a positive, upward trajectory.
Therefore, how can a business make informed decisions about its
locational choice in Seattle with this transit-oriented roadmap put in
place?
"""
)

st.divider()
st.subheader("Starting Assumptions")

st.markdown(
    """
Contemporary relocation trends increasingly suggest a rural exodus among
young people in developed nations. These trends point toward an inevitable
outcome of increased urban density, and all the logistical changes that
follow that outcome. American cities, long defined by the private vehicle
as a mode of transport, have been forced to consider adaptation strategies
to counteract increases in road traffic and a general decrease in the
desirability of car ownership in urban environments. One such adaptation
strategy is large-scale investment and development of modern public
transit hubs to better accommodate new urban residents. Lowering the
barrier to entry for these prospective residents by removing the absolute
need for a private vehicle is a great way to encourage continued
population growth without maximally straining existing transit
infrastructure.

Those trends raise the question this project takes up: what commercial
opportunities can be found near newly established transit hubs in a
built-out urban environment? On top of the
near-irreplaceable natural foot traffic stemming from these transit hubs,
nearby mixed-use or high-density housing developments typically follow
public transit developments. It is no secret that land and rent prices
increase when a neighborhood receives a convenient, well-connected hub to
the greater metro area. With those positive factors on valuation
established, a case can be made for furthering our understanding of
commercial density in relation to this increasingly popular transit
infrastructure phenomenon.
"""
)
