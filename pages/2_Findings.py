"""Findings page - the three analyses, with space for your written insight.

The charts are scaffolding. The prose sections marked TODO are the part a
reviewer actually reads; the numbers only set up what you argue.
"""

import pandas as pd
import streamlit as st

from config import RING_STATS_CSV, STATION_STATS_CSV, CHAIN_STATS_CSV, RING_LABELS

st.set_page_config(page_title="Findings", page_icon="📊", layout="wide")

st.title("Findings")

# --- 1. Distance gradient ---------------------------------------------

st.header("Does commercial density fall off with distance?")

if RING_STATS_CSV.exists():
    rings = pd.read_csv(RING_STATS_CSV)
    gradient = (
        rings.groupby("ring")["density_per_sq_mi"]
        .mean()
        .reindex(RING_LABELS)
    )
    st.bar_chart(gradient, y_label="Businesses per square mile")

    st.markdown(
        """
        **TODO — write this up.** Is the gradient monotonic? How steep? Which
        stations run against the pattern, and does the article's station-level
        commentary explain why? Rainier Beach is the case to check first: its
        commercial core sits several blocks from the platform, so a low reading
        there is geography rather than absence.
        """
    )

    with st.expander("Per-station detail"):
        st.dataframe(
            rings.pivot(index="station", columns="ring", values="density_per_sq_mi")
            .reindex(columns=RING_LABELS)
            .round(1),
            use_container_width=True,
        )
else:
    st.info("Run `python src/step4_rings.py` to generate ring statistics.")

# --- 2. Ridership ------------------------------------------------------

st.header("Does station volume track commercial density?")

if STATION_STATS_CSV.exists():
    stats = pd.read_csv(STATION_STATS_CSV)
    ridership_cols = [
        c for c in stats.columns
        if "boarding" in c.lower() or "ridership" in c.lower()
    ]

    if ridership_cols:
        col = ridership_cols[0]
        st.scatter_chart(
            stats, x=col, y="businesses_within_0_3mi",
            x_label="Average monthly boardings",
            y_label="Businesses within 0.3 miles",
        )
        clean = stats[[col, "businesses_within_0_3mi"]].dropna()
        if len(clean) > 2:
            r = clean.corr().iloc[0, 1]
            st.metric("Correlation", f"{r:.2f}")
            st.caption(
                f"n = {len(clean)} stations. Too few observations to support "
                "much beyond a description of the pattern."
            )

        st.markdown(
            """
            **TODO — write this up.** Whatever the correlation, the access-mode
            problem limits what it means: riders who arrive by car or connecting
            bus board without passing a storefront, so boardings overstate
            pedestrian exposure at park-and-ride and transfer-heavy stations.
            Northgate is the one to look at closely.
            """
        )
    else:
        st.info(
            "No ridership column found. Export station boardings from Sound "
            "Transit's dashboard to `data/raw/ridership_by_station.csv`, then "
            "re-run step 4. See data/raw/README.md."
        )
else:
    st.info("Run `python src/step4_rings.py` to generate station statistics.")

# --- 3. Chains ---------------------------------------------------------

st.header("Which brands bet on transit adjacency?")

if CHAIN_STATS_CSV.exists():
    chains = pd.read_csv(CHAIN_STATS_CSV)
    # "Chain" means 2+ real physical locations - NOT station_count > 1. A
    # single location inside the downtown buffer overlap (Westlake/Symphony/
    # Pioneer Square/International District) can touch up to 4 stations on
    # its own; that's the overlap, not a chain. Verified by hand in Session 6.
    multi = chains[chains["location_count"] > 1]

    left, right = st.columns(2)
    left.metric("Brands at more than one station", len(multi))
    right.metric(
        "Share of locations that are chains",
        f"{multi['location_count'].sum() / chains['location_count'].sum():.1%}"
        if len(chains) else "—",
    )

    st.dataframe(chains.head(25), use_container_width=True, hide_index=True)

    st.markdown(
        """
        **TODO — write this up.** A brand at eight stations has a real estate
        function making a repeated, deliberate bet on transit adjacency. A
        single-location shop may simply be where its owner could afford rent.
        Does the chain share rise as you move toward the platform? That would
        be the strongest single finding available here.

        Check the normalization by hand before trusting the counts — verify a
        few brands actually resolved correctly.
        """
    )
else:
    st.info("Run `python src/step4_rings.py` to generate chain statistics.")
