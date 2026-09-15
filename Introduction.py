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

st.subheader("What's here")

st.markdown(
    """
**Heatmap** — commercial density across the station areas, with the ring
boundaries drawn on.

**Findings** — the distance gradient, the relationship with station
ridership, and which brands appear at the most stations.

**Methodology** — where the data comes from, and what it cannot support.
Worth reading before the findings.
"""
)

if STATION_STATS_CSV.exists():
    stats = pd.read_csv(STATION_STATS_CSV)
    left, mid, right = st.columns(3)
    left.metric("Stations", len(stats))
    mid.metric(
        "Businesses within 0.3 mi",
        f"{int(stats['businesses_within_0_3mi'].sum()):,}",
    )
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
