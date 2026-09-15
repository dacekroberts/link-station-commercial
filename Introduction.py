"""Streamlit entry point.

Reads only from outputs/. Never runs the pipeline - that keeps the deployed
app free of the compiled geospatial stack, which is the usual reason a
Streamlit Cloud deploy fails.

Run:  streamlit run Introduction.py
"""

import pandas as pd
import streamlit as st

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

st.title("Commercial density around Seattle's light rail stations")

st.markdown(
    """
Businesses cluster near transit. Whether transit *causes* that clustering,
or lines get built where commerce already is, is harder to answer than a
map suggests.

This project measures commercial density in concentric rings around the
sixteen Link 1 Line stations inside Seattle, tests whether density falls
off with distance from the platform, and looks at which kinds of businesses
concentrate closest.
"""
)

st.subheader("Why Seattle?")

st.markdown(
    """
I have chosen to center on the Seattle area for this case study not only
because it is where I have been born, raised, and have become accustomed
to. More so, the city has several factors that make it an intriguing
option to explore this particular topic within. Firstly, the unparalleled
growth of the city, centered around its burgeoning tech sector has created
a slew of both exciting opportunities and concerns about existing
infrastructure's capacity for growth accommodation. Those concerns lean
into the second factor, which is a severe lack of centralized public
transit removed from privatized commuting costs. Before 2009, Seattle's
public transit was largely constrained to bus systems serving the wider
area, with only a select few downtown attractions housing fully integrated
transit networks. With buses as the legacy primary option for public
transit, the negative externalities of increased urban density on
transportation have uniformly affected all residents, whether or not they
own their own vehicle. Buses get stuck in traffic just as much as a
private vehicle, save for bus-only lanes which are not prevalent enough to
fully circumvent the high-density downsides. The end result is city
residents being stuck in a lose-lose situation: Either you brave the
traffic and put up with vehicle ownership or you budget an increased share
of time to afford walking to bus stops from your residence, waiting for
the bus, and dealing with the traffic's impacts regardless.

As a result, the introduction of the Link rail to the city's transit
infrastructure — first opened in 2009 and significantly expanded this
decade — has begun to change that equation. Starting with the subject of
this paper, the 1 Line serves the main network servicing the primary
north-south urban corridor. At the time of writing, the city has already
expanded into a 2nd line that serves an east-west area connecting the
greater King county's east side to the city of Seattle itself, suggesting
the local government is keen on furthering the reach and utility of the
Link rail. This firm stance should indicate to business owners that
support for the link rail, including attempts to increase ridership and
accessibility, are only set to continue on a positive, upwards trajectory.
Therefore, how can a business make informed decisions about their
locational choice in Seattle with this transit-oriented roadmap put in
place?
"""
)

st.subheader("What's here")

st.markdown(
    """
This project centers around a concentric ring analysis of commercial
density surrounding the city of Seattle's Link rail 1 line service area,
conducted across all 16 stations that fall within official Seattle city
limits. Business-license data, sourced directly from the City of Seattle's
own published open data, forms the commercial backbone of the analysis,
categorized by NAICS code. Additionally, ridership data per station is
included as a proxy for foot traffic levels around each station to
provide insights on potential commercial value. Lastly, chain analysis
was done to determine the level of chain presence within transit hub
localities. Concentric ring analysis has been visually published as a
dynamic heatmap viewable on the corresponding page. Resulting findings &
EDA, as well as Methodology & Limitations are similarly featured on their
own pages. Further analysis of 1 line stations outside of Seattle city
limits or the newer 2 line are not included at this time as an
appropriate scope limitation, though I am not discounting their addition
at a future time.
"""
)

if STATION_STATS_CSV.exists():
    stats = pd.read_csv(STATION_STATS_CSV)
    left, mid, right = st.columns(3)
    left.metric("Stations", len(stats))
    if CITYWIDE_COVERAGE_CSV.exists():
        coverage = pd.read_csv(CITYWIDE_COVERAGE_CSV).iloc[0]
        in_rings = int(coverage["businesses_in_rings"])
        citywide = int(coverage["businesses_citywide"])
        mid.metric(
            "Businesses within concentric ring area of Link stations",
            f"{in_rings:,} / {citywide:,} ({in_rings / citywide:.1%})",
        )
    else:
        mid.metric("Businesses within concentric ring area of Link stations", "—")
    right.metric("Business data", LICENSE_SNAPSHOT)
    st.caption(
        f"Ridership figures reflect {RIDERSHIP_SNAPSHOT}. The gap between the "
        "two dates is discussed on the methodology page."
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
st.subheader("Starting Assumptions")
st.caption(
    "Framing, not findings - my own lens coming in, not a claim this "
    "project's data backs up. See Methodology for what the data actually "
    "supports."
)

st.markdown(
    """
Through my relevant education and research, I've come to believe
contemporary relocation trends increasingly suggest a rural exodus amongst
young people in developed nations. These trends point towards an inevitable
outcome of increased urban density, and all the logistical changes that
follow that outcome. American cities long-defined by the private vehicle as
a mode of transport have been forced to consider adaptation strategies to
counteract increases in road traffic and a general decrease in desirability
to manage car ownership in urban environments. One such adaptation strategy
is large-scale investment and development of modern public transit hubs to
better accommodate new urban residents. Lowering the barrier to entry for
these prospective residents by removing the absolute need of a private
vehicle is a great way to encourage continued population growth without
maximally straining existing transit infrastructure.

After studying these concepts in my collegiate Urban Economics and
Philosophy of Economics courses, I felt compelled to drive an investigation
into the commercial opportunities one could find out of newly established
transit hubs in a built-out urban environment. On top of the
near-irreplacable natural foot traffic stemming from these transit hubs,
nearby mixed-use or high-density housing developments typically follow
public transit developments. It is no secret that land and rent prices
increase when a neighborhood receives a convenient, well-connected hub to
the greater metro area. With those positive factors on valuation
established, a case can be made for furthering our understanding of
commercial density in relation to this increasingly popular transit
infrastructure phenomenon.
"""
)
