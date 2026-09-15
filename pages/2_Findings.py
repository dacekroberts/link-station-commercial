"""Findings page - the three analyses, with space for your written insight.

The charts are scaffolding. The prose sections marked TODO are the part a
reviewer actually reads; the numbers only set up what you argue.
"""

import altair as alt
import pandas as pd
import streamlit as st

from config import RING_STATS_CSV, STATION_STATS_CSV, CHAIN_STATS_CSV, RING_LABELS, STATIONS_CSV

st.set_page_config(page_title="Findings", page_icon="📊", layout="wide")

st.title("Findings")

# --- 1. Distance gradient ---------------------------------------------

st.header("Concentric Ring Gradient Analysis")
st.caption("Does commercial density fall off with distance?")

if RING_STATS_CSV.exists():
    rings = pd.read_csv(RING_STATS_CSV)
    gradient = (
        rings.groupby("ring")["density_per_sq_mi"]
        .mean()
        .reindex(RING_LABELS)
    )
    # "Ring 1: 0-0.1 mi" etc., shared by this chart, the per-station chart
    # below, and the per-station table further down.
    numbered_ring_labels = [f"Ring {i + 1}: {label}" for i, label in enumerate(RING_LABELS)]
    ring_number_map = dict(zip(RING_LABELS, numbered_ring_labels))

    st.markdown("**Average businesses/sq mi per Concentric Ring**")
    gradient_df = gradient.rename("density_per_sq_mi").reset_index()
    gradient_df["ring_label"] = gradient_df["ring"].map(ring_number_map)
    # Built directly in Altair, not st.bar_chart - st.bar_chart's y_label
    # and the underlying column name each generate their own tooltip
    # field, showing the same number twice under two different labels.
    # Explicit tooltips here match the per-station line chart's exactly:
    # Ring + Businesses/sq mi, same titles, same .0f rounding.
    bar_chart = (
        alt.Chart(gradient_df)
        .mark_bar()
        .encode(
            x=alt.X("ring_label:N", sort=numbered_ring_labels, title="Ring"),
            y=alt.Y("density_per_sq_mi:Q", title="Businesses per square mile"),
            tooltip=[
                alt.Tooltip("ring_label:N", title="Ring"),
                alt.Tooltip("density_per_sq_mi:Q", title="Businesses/sq mi", format=".0f"),
            ],
        )
    )
    st.altair_chart(bar_chart, use_container_width=True)

    # Per-station view: which stations follow the expected declining
    # pattern, and which run against it. Classification rule, computed
    # from the data rather than picked by eye: a station counts as
    # "standard" if its density never climbs back above its own ring-1
    # level after the first ring - one minor up-tick along the way still
    # counts as this pattern (real noise), but a station that re-exceeds
    # its own ring-1 density, or starts at zero there, counts as against
    # the pattern. The two groups happen to split the sixteen stations
    # exactly in half.
    station_pivot = (
        rings.pivot(index="station", columns="ring", values="density_per_sq_mi")
        .reindex(columns=RING_LABELS)
    )

    def _classify(row):
        vals = row.to_numpy()
        first = vals[0]
        if pd.isna(first) or first == 0:
            return "Against the pattern"
        if any(pd.notna(v) and v > first for v in vals[1:]):
            return "Against the pattern"
        return "Standard pattern"

    station_group = station_pivot.apply(_classify, axis=1)
    long = rings[["station", "ring", "density_per_sq_mi"]].assign(
        group=lambda d: d["station"].map(station_group),
        ring_label=lambda d: d["ring"].map(ring_number_map),
    )
    n_standard = int((station_group == "Standard pattern").sum())
    n_against = int((station_group == "Against the pattern").sum())

    st.caption(
        f"{n_standard} of 16 stations never climb back above their own "
        f"ring-1 density after the first ring (a single minor up-tick still "
        f"counts as this pattern - a real reversal doesn't); the other "
        f"{n_against} run against it. Hover a line for the station name."
    )

    per_station_chart = (
        alt.Chart(long)
        .mark_line(point=True)
        .encode(
            x=alt.X("ring_label:N", sort=numbered_ring_labels, title="Ring"),
            y=alt.Y("density_per_sq_mi:Q", title="Businesses per square mile"),
            detail="station:N",
            color=alt.Color(
                "group:N",
                title=None,
                scale=alt.Scale(
                    domain=["Standard pattern", "Against the pattern"],
                    range=["#4c78a8", "#e45756"],
                ),
                legend=alt.Legend(
                    orient="top-left",
                    direction="vertical",
                    fillColor="#0e1117",
                    padding=4,
                    offset=0,
                    symbolSize=40,
                    labelFontSize=9,
                    labelLimit=90,
                    rowPadding=1,
                ),
            ),
            opacity=alt.condition(
                alt.datum.group == "Against the pattern",
                alt.value(0.9),
                alt.value(0.45),
            ),
            tooltip=[
                alt.Tooltip("station:N", title="Station"),
                alt.Tooltip("ring_label:N", title="Ring"),
                alt.Tooltip("density_per_sq_mi:Q", title="Businesses/sq mi", format=".0f"),
            ],
        )
        .properties(height=504, width=900, padding={"bottom": 90})
    )
    # Fixed width (not container-filling), capped at 900px deliberately -
    # measured (not guessed) that Streamlit's main content container caps
    # out at 970px on a 1280px-wide window with the sidebar expanded;
    # anything wider than that drags the whole page into horizontal
    # scroll, not just this chart, since a scoped-scroll wrapper (tried via
    # unsafe_allow_html, the same idea as the heatmap iframe's own
    # scrolling=True) doesn't work in this Streamlit version - each
    # st.markdown/st.altair_chart call gets its own isolated element
    # container rather than nesting inside a shared open tag. 900px leaves
    # a margin under the measured ceiling and is still meaningfully wider
    # than the ~810px this chart rendered at under container-fill, short of
    # the originally-requested 1.5x (which would need ~1200px) - traded
    # off in favor of a page that doesn't scroll sideways on a normal
    # laptop window.
    st.altair_chart(per_station_chart, use_container_width=False)

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
        # Same 8/8 split and colour as the line chart above: standard-
        # pattern stations first, against-the-pattern stations after,
        # alphabetical within each group; against-the-pattern station
        # names coloured to match their line ("#e45756").
        detail = (
            rings.pivot(index="station", columns="ring", values="density_per_sq_mi")
            .reindex(columns=RING_LABELS)
            .round(0)
        )
        # North-to-south within each group, not alphabetical - Link 1 Line
        # runs roughly north-south, so this reads as a trip down the line
        # rather than an arbitrary A-Z list. Real station coordinates, not
        # a guessed geographic order.
        station_order = (
            pd.read_csv(STATIONS_CSV).sort_values("latitude", ascending=False)["station"].tolist()
        )
        ordered_index = (
            [s for s in station_order if station_group.get(s) == "Standard pattern"]
            + [s for s in station_order if station_group.get(s) == "Against the pattern"]
        )
        # station moved out of the index into a plain column - Streamlit's
        # dataframe grid doesn't forward Styler.map_index() colour to the
        # index column (tried it, confirmed via direct DOM inspection: text
        # stayed default white), but does respect column-cell styling via
        # Styler.map() on a regular column.
        detail = (
            detail.reindex(ordered_index)
            .reset_index()
            .rename(columns={"station": "Station Name", **ring_number_map})
        )

        def _highlight_against(station_name):
            if station_group.get(station_name) == "Against the pattern":
                return "color: #e45756; font-weight: 600;"
            return ""

        # na_rep isn't honoured by Streamlit's dataframe grid for missing
        # values (tested directly against pandas' own HTML output: the
        # substitution works at the pandas level, Streamlit's canvas-
        # rendered grid just doesn't use it) - null cells show as "None"
        # rather than an em dash. Converting the column to pre-formatted
        # strings would fix that but make column-sort lexicographic
        # instead of numeric (e.g. "900" sorting after "1000"), not worth
        # trading for a cosmetic nicety.
        st.dataframe(
            detail.style
            .map(_highlight_against, subset=["Station Name"])
            .format("{:.0f} businesses/sq mi", subset=numbered_ring_labels),
            use_container_width=True,
            hide_index=True,
        )

    # Breaks down the aggregate bar chart's ring-3 uptick: how many of the
    # 16 stations actually rise from ring 2 to ring 3 (rather than
    # continuing to decline), and how many of those are from the
    # against-the-pattern group vs. the standard-pattern group. Computed
    # from station_pivot/station_group, already built above for the
    # chart and table - not re-derived.
    ring2_col, ring3_col = RING_LABELS[1], RING_LABELS[2]
    ring3_uptick = station_pivot[ring3_col] > station_pivot[ring2_col]
    contributors = station_pivot[ring3_uptick].index
    n_contributors = len(contributors)
    n_against_contributors = int((station_group.loc[contributors] == "Against the pattern").sum())
    against_names = sorted(
        s for s in contributors if station_group.loc[s] == "Against the pattern"
    )

    ring2_avg = gradient[ring2_col]
    ring3_avg = gradient[ring3_col]
    st.markdown(
        f"**Ring 3 uptick, broken down:** {n_contributors} of 16 stations have "
        f"higher density in ring 3 than ring 2 - this is what pulls the aggregate "
        f"chart above up at ring 3 instead of continuing to decline. "
        f"**{n_against_contributors} of those {n_contributors}** are from the "
        f"against-the-pattern group ({', '.join(against_names)}), not the "
        f"standard-pattern group. In absolute terms, the aggregate rises from "
        f"{ring2_avg:.0f} to {ring3_avg:.0f} businesses/sq mi - a "
        f"{ring3_avg - ring2_avg:.0f}-business-per-sq-mi difference."
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
