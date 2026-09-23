"""Findings page - the three analyses, with space for your written insight.

The charts are scaffolding. The prose sections marked TODO are the part a
reviewer actually reads; the numbers only set up what you argue.
"""

import altair as alt
import pandas as pd
import streamlit as st

from components import (
    render_sidebar_nav_label,
    render_social_links,
    set_base_font,
    set_sidebar_width,
)
from config import (
    RING_STATS_CSV,
    STATION_STATS_CSV,
    CHAIN_STATS_CSV,
    CHAIN_RING_STATS_CSV,
    RING_LABELS,
    SEATTLE_1LINE_STATIONS,
)

# The "against the pattern" red: Graph 2's lines and legend, Table 1's
# station names, and the station write-up headers all share it, so tuning it
# (e.g. to keep it distinct from the warm theme's orange, see
# .streamlit/config.toml) is a one-line change.
AGAINST_RED = "#e45756"

# Static legend/schematic for Graph 1 - explains what "Concentric Ring 1-4"
# means before the reader hits the bar chart. Pure decoration, no data
# dependency, so it's a plain constant rather than something built from
# RING_LABELS - its four ring colors must stay in sync with `ring_colors`
# below, which colors Graph 1 and Graph 5's bars. Sized as a narrow vertical
# layout (300x450 viewBox) to
# sit legibly in the slim right-hand column next to Graph 1, rather than the
# wide horizontal layout that would suit a full-width placement.
# One unbroken block, no blank lines: Streamlit's markdown renderer follows
# CommonMark's rule that a raw-HTML block (an <svg> isn't on the "continue
# until closing tag" whitelist that <script>/<pre>/<style> get) ends at the
# first blank line - anything after was silently dropped when this had blank
# lines between element groups for readability.
# fill="currentColor" (not a hardcoded hex) on the label text so it inherits
# the page's actual text color and stays legible in both the light and dark
# Streamlit themes - the ring/marker fills stay hardcoded since those sit on
# their own solid color and don't depend on the page theme.
RING_SCHEMATIC_SVG = (
    '<svg width="100%" viewBox="0 0 300 450" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="Schematic of the four concentric rings used in this analysis">'
    '<text x="150" y="20" text-anchor="middle" font-size="14" font-weight="600" fill="currentColor">Schematic 1:</text>'
    '<text x="150" y="38" text-anchor="middle" font-size="14" font-weight="600" fill="currentColor">Concentric Ring Diagram</text>'
    '<circle cx="150" cy="150" r="80" fill="#FDD0A2"/>'
    '<circle cx="150" cy="150" r="60" fill="#FBB878"/>'
    '<circle cx="150" cy="150" r="40" fill="#F0801F"/>'
    '<circle cx="150" cy="150" r="22" fill="#C2500A"/>'
    '<circle cx="150" cy="150" r="4" fill="#FFFFFF" stroke="#2C2C2A" stroke-width="1.5"/>'
    '<text x="150" y="143" text-anchor="middle" font-size="14" font-weight="600" fill="#FFFFFF">1</text>'
    '<text x="150" y="123" text-anchor="middle" font-size="14" font-weight="600" fill="#3B1505">2</text>'
    '<text x="150" y="104" text-anchor="middle" font-size="14" font-weight="600" fill="#3B1505">3</text>'
    '<text x="150" y="84" text-anchor="middle" font-size="14" font-weight="600" fill="#3B1505">4</text>'
    '<text x="150" y="248" text-anchor="middle" font-size="11" fill="currentColor" opacity="0.6">not to scale</text>'
    '<circle cx="18" cy="278" r="8" fill="#FFFFFF" stroke="#2C2C2A" stroke-width="1.5"/>'
    '<text x="34" y="282" font-size="13" fill="currentColor">Origin Point (Station</text>'
    '<text x="34" y="298" font-size="13" fill="currentColor">Coordinates)</text>'
    '<rect x="10" y="312" width="16" height="16" rx="3" fill="#C2500A"/>'
    '<text x="34" y="324" font-size="13" fill="currentColor">Concentric Ring 1: 0-0.1 mi</text>'
    '<rect x="10" y="346" width="16" height="16" rx="3" fill="#F0801F"/>'
    '<text x="34" y="358" font-size="13" fill="currentColor">Concentric Ring 2: 0.1-0.2 mi</text>'
    '<rect x="10" y="380" width="16" height="16" rx="3" fill="#FBB878"/>'
    '<text x="34" y="392" font-size="13" fill="currentColor">Concentric Ring 3: 0.2-0.3 mi</text>'
    '<rect x="10" y="414" width="16" height="16" rx="3" fill="#FDD0A2"/>'
    '<text x="34" y="426" font-size="13" fill="currentColor">Concentric Ring 4: 0.3-0.6 mi</text>'
    "</svg>"
)

st.set_page_config(page_title="Findings", page_icon="📊", layout="wide")

set_base_font()
set_sidebar_width()
render_sidebar_nav_label()
render_social_links()

st.title("Findings & EDA")
st.caption("EDA: Exploratory Data Analysis")

# --- 1. Distance gradient ---------------------------------------------

st.header("Concentric Ring Gradient Analysis")
st.caption(
    "<u>All visuals on this page are interactive. Hover over data points "
    "for detailed information.</u>",
    unsafe_allow_html=True,
)

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

    # Same 4 hex values as Schematic 1's rings (a warm orange ramp, bold
    # burnt orange at ring 1 to soft peach at ring 4) so the bar colors below
    # read as the same rings. Stays inside orange and peach on purpose:
    # no red (Graph 2's against-pattern lines, Table 1's highlight) and no
    # true yellow (Graph 4's Ridership dots).
    ring_colors = ["#C2500A", "#F0801F", "#FBB878", "#FDD0A2"]

    chart_col, schematic_col = st.columns([3, 1])

    with chart_col:
        st.markdown("**Graph 1: Average businesses/sq mi per Concentric Ring**")
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
                x=alt.X(
                    "ring_label:N",
                    sort=numbered_ring_labels,
                    title="Concentric Ring",
                    axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, ': ')[0]"),
                ),
                y=alt.Y("density_per_sq_mi:Q", title="Businesses per square mile"),
                color=alt.Color(
                    "ring_label:N",
                    sort=numbered_ring_labels,
                    scale=alt.Scale(domain=numbered_ring_labels, range=ring_colors),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("ring_label:N", title="Ring"),
                    alt.Tooltip("density_per_sq_mi:Q", title="Businesses/sq mi", format=".0f"),
                ],
            )
        )
        st.altair_chart(bar_chart, width="stretch")

    with schematic_col:
        st.markdown(RING_SCHEMATIC_SVG, unsafe_allow_html=True)

    # Ring-to-ring percent change, computed from the same `gradient` series
    # the chart above renders - not hardcoded, so it stays accurate if the
    # underlying data changes.
    r1, r2, r3, r4 = (gradient[label] for label in RING_LABELS)
    st.caption(
        f"Ring-to-ring change: Ring 1→2 {(r2 - r1) / r1:+.1%}, "
        f"Ring 2→3 {(r3 - r2) / r2:+.1%} (the uptick), "
        f"Ring 3→4 {(r4 - r3) / r3:+.1%}."
    )

    st.markdown(
        """
        Graph 1 aligns with one of my hypotheses when starting this project:
        "Does commercial density drop off with decreased proximity to
        transit hubs"? The overall density between concentric rings 1 to 4
        shows a net decrease of -62.9% (837 businesses/sq mi → 310).
        On its own, this would appear to support my hypothesis, but
        looking closer at the data reveals a contradiction. The slight jump
        (+0.9%) between rings 2 and 3 would seem to suggest that, although
        density does drop off on a macro-level, the decay is not
        monotonic. What causes this mid-level rise?
        """
    )

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

    st.markdown("**Graph 2: Per-station Commercial Density by Concentric Ring**")
    st.caption(
        f"{n_standard} of 16 stations never climb back above their own "
        f"ring-1 density after the first ring (a single minor up-tick still "
        f"counts as this pattern; a real reversal doesn't); the other "
        f"{n_against} run against it. Hover a line for the station name."
    )

    per_station_chart = (
        alt.Chart(long)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "ring_label:N",
                sort=numbered_ring_labels,
                title="Concentric Ring",
                axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, ': ')[0]"),
            ),
            y=alt.Y("density_per_sq_mi:Q", title="Businesses per square mile"),
            detail="station:N",
            color=alt.Color(
                "group:N",
                title=None,
                scale=alt.Scale(
                    domain=["Standard pattern", "Against the pattern"],
                    range=["#4c78a8", AGAINST_RED],
                ),
                legend=alt.Legend(
                    orient="top",
                    direction="horizontal",
                    offset=8,
                    symbolSize=60,
                    labelFontSize=11,
                    columnPadding=16,
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
        .properties(height=504)
    )
    # Container-width, not a fixed pixel width. This chart used to be pinned
    # at 900px (a laptop-window choice: wider than the ~810px container-fill
    # size, but under the 970px ceiling that would drag the whole page into
    # horizontal scroll). On a phone that fixed width overflowed a ~343px
    # container with nothing to scroll it, cutting off Rings 2-4 entirely
    # (measured at a 375px viewport). Filling the container is the fix; the
    # legend moved above the plot (horizontal) so it no longer overlays the
    # lines at narrow widths, which also made its old opaque dark fill, a
    # hardcoded copy of the theme background, unnecessary.
    st.altair_chart(per_station_chart, width="stretch")

    st.markdown(
        """
        To answer the rise between concentric rings 2 and 3 found in Graph
        1, I constructed a line Graph, per station, for Graph 2 to get a
        visual on which stations adhered to the "pattern" of top-down (but
        not strictly linear) decay. As it turns out, the stations split in
        half when checking their adherence. Eight Stations (neutral color)
        mostly correlated to a decay pattern, and the other eight (red)
        eclipsed their ring 1 totals further away. With this discovery in
        mind, I constructed Table 1 (below) to get an itemized view of the
        commercial density data per station. I found that six out of
        sixteen stations exhibited a ring 2 → ring 3 rise, and of those
        six stations, four were a part of the against-pattern group. At
        this point, I was certain I could provide an explanation for the
        ring 2->3 rise if I could also explain the reasoning for the
        against-pattern station group. I decided that taking a look at each of
        these eight stations individually was the best course of action.
        """
    )

    with st.expander("Table 1: Commercial Density by Concentric Ring"):
        # Same 8/8 split and color as the line chart above: standard-
        # pattern stations first, against-the-pattern stations after,
        # alphabetical within each group; against-the-pattern station
        # names colored to match their line (AGAINST_RED).
        detail = (
            rings.pivot(index="station", columns="ring", values="density_per_sq_mi")
            .reindex(columns=RING_LABELS)
            .round(0)
        )
        # North-to-south within each group, not alphabetical - Link 1 Line
        # runs roughly north-south, so this reads as a trip down the line
        # rather than an arbitrary A-Z list. SEATTLE_1LINE_STATIONS (config.py)
        # is already in that order, verified against real station coordinates
        # in step1_stations.py - not data/processed/stations.csv directly,
        # which is a gitignored pipeline intermediate that doesn't exist on
        # Streamlit Cloud (this was a real bug: FileNotFoundError in
        # production, since the app is only supposed to read outputs/).
        station_order = list(SEATTLE_1LINE_STATIONS)
        ordered_index = (
            [s for s in station_order if station_group.get(s) == "Standard pattern"]
            + [s for s in station_order if station_group.get(s) == "Against the pattern"]
        )
        # station moved out of the index into a plain column - Streamlit's
        # dataframe grid doesn't forward Styler.map_index() color to the
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
                return f"color: {AGAINST_RED}; font-weight: 600;"
            return ""

        # No null cells: step 4 writes an empty ring as a row with 0
        # businesses rather than omitting it, so Northgate/UW ring 1 and
        # Rainier Beach ring 3 show "0 businesses/sq mi". (They used to be
        # missing rows and rendered as "None" - Streamlit's grid ignores
        # na_rep.)
        st.dataframe(
            detail.style
            .map(_highlight_against, subset=["Station Name"])
            .format("{:.0f} businesses/sq mi", subset=numbered_ring_labels),
            width="stretch",
            hide_index=True,
        )

    # Per-station write-up, one collapsible <details> per station/pair.
    # Not st.expander() - its label is plain text only (no markdown/HTML),
    # so it can't take the red-for-against-pattern color, underline, or
    # larger font this section asks for. <details>/<summary> gives native
    # collapse/expand behavior with full control over header styling
    # instead. Red is AGAINST_RED, the same color used for against-pattern
    # station names in Table 1 and the Graph 2 lines and legend (a plain
    # string with a placeholder, not an f-string, since the CSS braces would
    # all need doubling).
    st.markdown(
        """
        <style>
        .station-note summary {
            font-weight: 700;
            text-decoration: underline;
            font-size: 1.15rem;
            cursor: pointer;
            margin: 0.75rem 0 0.25rem 0;
        }
        .station-note.against summary { color: __AGAINST_RED__; }
        .station-note p { margin: 0.35rem 0 1rem 0; }
        </style>
        """.replace("__AGAINST_RED__", AGAINST_RED),
        unsafe_allow_html=True,
    )

    station_notes = [
        {
            "title": "Northgate",
            "against": True,
            "body": """Northgate station has zero businesses within its first concentric
                ring. That alone sets it into the red group. If we look at the heatmap
                (or any map, for that matter), it's easy to see why: Interstate 5 sits
                directly west of the station coordinates, swallowing up roughly half
                of the potential area for commercial density immediately. On the east
                side, the station's parking absorbs the remaining possible land for
                businesses, which flags Northgate as an urban geographic victim within
                this experiment. There is simply more important infrastructure that
                already exists in the station's proximity, hindering next-door
                commercial development potential.""",
        },
        {
            "title": "University of Washington",
            "against": True,
            "body": """This station exits adjacent to UW's Husky Stadium and the
                Montlake UW Hospital campus, both of which are vast and long-term
                spatial occupiers in the area. As a result, there are once again zero
                businesses within its first concentric ring. Similar to Northgate, the
                existing urban design predating the light rail's implementation has
                limited the possibility of proximal commercial space in this area.""",
        },
        {
            "title": "Westlake/Symphony",
            "against": True,
            "body": """Both stations sit very close to each other in Seattle's densest
                downtown area. So close, in fact, that their third concentric rings
                overlap on each other's origin points (station coordinates). This
                station-to-station proximity reveals a limitation in my density model:
                Businesses that sit between two close stations, as in this instance,
                will be counted twice, meaning the ring 3 commercial density jump for
                one station largely comes from counting businesses clustered around
                another station.""",
        },
        {
            "title": "Pioneer Square",
            "against": True,
            "body": """Similar to Westlake/Symphony, being the next station down in the
                packed downtown corridor with a commercial density increase from
                concentric ring 1-&gt;2 rather than 2-&gt;3. Indicative of the
                persistent double-counting of businesses due to station proximity. Sits
                directly next to public-serving infrastructure like Seattle Civic
                Square, King County courthouse, and City Hall Park, limiting adjacent
                commercial development.""",
        },
        {
            "title": "Stadium",
            "against": True,
            "body": """Uniquely placed station with primary purpose being to serve
                sports fans for football, soccer, and baseball at Lumen Field/T-Mobile
                Park. The surrounding area has been reserved for Metro
                operations/employees and not catered toward spontaneous foot traffic.
                Concentric Ring 4 touches Chinatown Station, which spikes commercial
                density there.""",
        },
        {
            "title": "SODO",
            "against": True,
            "body": """SODO station sits in a historically industrial corridor of
                Seattle. Lots of adjacent auto-related businesses, back offices, etc.
                Like the stadium station, the area is not very foot-traffic
                friendly.""",
        },
        {
            "title": "Rainier Beach",
            "against": True,
            "body": """Intriguing from a geography perspective, Rainier Beach station
                sits multiple blocks away from the neighborhood's main commercial
                core, resulting in zero business in concentric ring 3. Other possible
                factors include the nearby East Duwamish Greenbelt and sprawling
                residential/scholastic developments in place of commercial zones.""",
        },
        {
            "title": "Beacon Hill/Mount Baker",
            "against": False,
            "body": """Although these two stations do not fall into the against
                pattern group, it is worth mentioning that their concentric ring 4
                boundaries barely miss the other station. This generated a weaker
                version of the spacing effects seen in the downtown stations, but not
                to a large enough degree to go against the pattern.""",
        },
        {
            "title": "Capitol Hill",
            "against": False,
            "body": """Another station in the pattern-adhering group, despite having a
                concentric ring 2-&gt;3 jump like in Graph 1. The best reasonable
                explanation is that, for as dense a location as Capitol Hill, having
                concentric ring 2 absorbing the bulk of Cal Anderson Park, the largest
                of its kind in the area, potentially skews the density data. I feel
                more confident in this explanation based on the fact that even ring 4
                outperforms ring 2 in terms of commercial density in this regard.""",
        },
        {
            "title": "Columbia City",
            "against": False,
            "body": """Columbia City features a dense residential zone in its midst,
                resulting in another commercial jump from concentric ring 2-&gt;3.
                Since it falls within the pattern-adhering group nonetheless, I
                believe there could be a potential pattern between residential cores
                and a ring 2-&gt;3 jump based on there simply being more surface area
                for ring 3 to draw a few more businesses.""",
        },
    ]
    for note in station_notes:
        css_class = "station-note against" if note["against"] else "station-note"
        st.markdown(
            f"""
            <details class="{css_class}">
            <summary>{note['title']}</summary>
            <p>{note['body']}</p>
            </details>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<h3 style="font-size:1.5rem;">Gradient: Concluding Thoughts</h3>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        After thoroughly investigating the eight stations against the
        density decay pattern (alongside a few extra), two main factors
        stood out to me as explanations for their non-conformity and the
        concentric ring 2->3 rise. The first is geographic limitations.
        Seattle is already a uniquely constrained city due to its isthmus
        shape (narrow stretch of land with water bodies on both sides),
        meaning not all transit stops are blessed with an adjacent
        commercially viable zone. This is especially true when we consider
        how long existing Seattle infrastructure has been in place prior
        to the rapid 1 line expansion this decade. Northgate, UW, Stadium,
        SODO, and Rainier Beach all suffer from urban geographic
        limitations.

        The second factor also stems from urban geography, differing in
        its direct impact on my methodology in interpreting the data. I
        coined this phenomenon "downtown buffer overlap", and the three
        downtown stations of Westlake, Symphony, and Pioneer Square are its
        representatives. Rather than seeing downtown buffer overlap as
        disproving my hypothesis, I believe it shows potential for
        improving the density model in future iterations of this project.
        One quick fix I ruled out would be to assign businesses to
        one station, whichever is closest. This is implemented on the
        heatmap when zooming in to look at individual businesses, but from
        a macro standpoint it doesn't make sense to do so. Someone could
        get off at the Symphony Station, walk around downtown, and do some
        shopping near Westlake. Those sorts of interactions shouldn't be
        discounted just because the shopper got off at a slightly further
        station.
        """
    )

else:
    st.info("Run `python src/step4_rings.py` to generate ring statistics.")

# --- 2. Ridership ------------------------------------------------------

st.divider()
st.header("Ridership Analysis")

if STATION_STATS_CSV.exists():
    stats = pd.read_csv(STATION_STATS_CSV)
    ridership_cols = [
        c for c in stats.columns
        if "boarding" in c.lower() or "ridership" in c.lower()
    ]

    if ridership_cols:
        col = ridership_cols[0]
        clean = stats[["station", col, "businesses_within_0_3mi"]].dropna()
        if len(clean) > 2:
            r = clean[[col, "businesses_within_0_3mi"]].corr().iloc[0, 1]
            st.markdown("**Graph 3: Commercial Density VS Station Ridership Volume**")
            st.caption(
                f"n = {len(clean)} stations. Too few observations to support "
                "much beyond a description of the pattern."
            )
            with st.popover("How to read this chart"):
                st.markdown(
                    "Each dot is one of the sixteen stations, placed by its "
                    "average monthly boardings (x-axis) against the number "
                    "of businesses within 0.3 miles of it (y-axis). The "
                    "dashed line is a least-squares trendline through all "
                    "sixteen points, showing the overall direction of the "
                    "relationship. Hover a dot for that station's name and "
                    "exact numbers."
                )

            # Single color, no legend - only 2 of 16 stations (UW,
            # Northgate) are access-mode outliers, not enough to warrant a
            # color split. Station names still available via tooltip.
            base = alt.Chart(clean)
            points = base.mark_circle(size=110, color="#4c78a8").encode(
                x=alt.X(f"{col}:Q", title="Average monthly boardings"),
                y=alt.Y("businesses_within_0_3mi:Q", title="Businesses within 0.3 miles"),
                tooltip=[
                    alt.Tooltip("station:N", title="Station"),
                    alt.Tooltip(f"{col}:Q", title="Avg. Monthly Boardings", format=","),
                    alt.Tooltip(
                        "businesses_within_0_3mi:Q", title="Businesses Within 0.3mi", format=","
                    ),
                ],
            )
            # Visually anchors the r=0.68 correlation reported above - a
            # least-squares fit through all 16 points, not a claim of
            # causation.
            trend = base.transform_regression(
                col, "businesses_within_0_3mi"
            ).mark_line(strokeDash=[4, 4], strokeWidth=3, opacity=1).encode(
                x=alt.X(f"{col}:Q"),
                y=alt.Y("businesses_within_0_3mi:Q"),
                color=alt.value("#4c78a8"),
            )
            st.altair_chart(
                (points + trend).properties(height=420),
                width="stretch",
            )
            st.subheader("Correlation")
            st.markdown(f"**r = {r:.3f}**")
            # How much does r depend on a single high-leverage point? Not
            # redundant with the CV/dot-plot material further down (that's
            # about each variable's own spread; this is about the
            # correlation's robustness) - Westlake is the single highest
            # station in both ridership and density at once, so it's the
            # natural leverage check. Computed here, not hardcoded, so it
            # stays accurate if the underlying data changes.
            no_westlake = clean[clean["station"] != "Westlake"]
            r_no_westlake = no_westlake[[col, "businesses_within_0_3mi"]].corr().iloc[0, 1]
            r_spearman = clean[col].rank().corr(clean["businesses_within_0_3mi"].rank())
            st.caption(
                f"Westlake is the single highest station in both ridership and "
                f"density. Removing it drops r from {r:.3f} to {r_no_westlake:.3f}. "
                f"The rank-based (Spearman) correlation across all 16 stations is "
                f"only {r_spearman:.3f}. Part of the observed linear relationship "
                "depends on this one high-leverage point rather than reflecting a "
                "consistent pattern across every station."
            )

        st.markdown(
            """
            The method I used to attempt proxying genuine foot traffic in
            Seattle's transit corridor was to use average monthly
            ridership counts per station, as direct commercial data from
            storefronts is often privatized or sold at scale. This metric
            comes with a fair bit of concern around whether all boardings
            at a given station correlate with commercial value, as there
            is not an additional mechanism in place, such as a survey, to
            indicate trip purpose per passenger. Regardless, we can draw a
            relative correlation between higher volume and higher earnings
            potential for nearby businesses. On the business end, 0.3 mi
            was used as a representative cutoff, summing the first three
            rings, for each station under the concentric ring model.

            Graph 3's scatter and trendline suggest a moderately strong
            correlation (r=0.684) between ridership volume and business
            density per station. As mentioned in the caption, however, the
            station of Westlake being the highest boarded and having the
            most businesses heavily skews the correlation. After making
            this discovery, I determined that having a table ranking stations
            based on ridership could give insight into other potential
            outliers within this correlation.
            """
        )

        with st.expander("Table 2: Link Stations Ranked by Average Monthly Ridership"):
            ridership_detail = (
                stats[["station", col, "businesses_within_0_3mi"]]
                .rename(columns={
                    "station": "Station Name",
                    col: "Avg. Monthly Boardings",
                    "businesses_within_0_3mi": "Businesses Within 0.3mi",
                })
                .sort_values("Avg. Monthly Boardings", ascending=False)
                .reset_index(drop=True)
            )
            ridership_detail.index += 1
            ridership_detail.index.name = "Rank"
            st.dataframe(
                ridership_detail.style.format(
                    "{:,.0f}", subset=["Avg. Monthly Boardings", "Businesses Within 0.3mi"]
                ),
                width="stretch",
            )

        # ridership_rank feeds the Symphony/Pioneer Square caption below.
        ridership_rank = clean[col].rank(ascending=False)

        # Symphony and Pioneer Square are the inverse of the UW/Northgate
        # mismatch discussed in the write-up below: solidly mid-pack on
        # ridership but 2nd/3rd-highest density of all 16 stations.
        # Computed from the same ridership-rank basis as the rest of this
        # section, not hardcoded.
        symphony = clean[clean["station"] == "Symphony"].iloc[0]
        pioneer = clean[clean["station"] == "Pioneer Square"].iloc[0]
        symphony_rank = int(ridership_rank[clean["station"] == "Symphony"].iloc[0])
        pioneer_rank = int(ridership_rank[clean["station"] == "Pioneer Square"].iloc[0])
        st.caption(
            f"Symphony (rank {symphony_rank}) and Pioneer Square (rank {pioneer_rank}) "
            f"feature "
            f"{symphony['businesses_within_0_3mi']:.0f} and "
            f"{pioneer['businesses_within_0_3mi']:.0f} businesses within 0.3mi, the "
            "2nd- and 3rd-highest of all 16, despite mid-pack ridership. Both sit in "
            "the downtown overlap cluster, so some of that density is buffer "
            "inflation, not purely organic."
        )

        st.markdown(
            """
            Table 2 revealed a plethora of outliers, albeit none as
            extreme as Westlake from a raw numbers perspective. Rather,
            the ranking of ridership and resulting business values showed
            some signs of promise for a stronger correlation, and some
            detractors as well. First, the promising side: Of the seven
            stations with triple-digit business counts nearby, five were
            in the top seven by ridership volume as well. In a vacuum,
            this stat should affirm a correlation between business
            density and ridership. However, looking at the rest of the
            data is where the realistic picture gets formed.

            Sitting in fifth and seventh place by ridership volume are UW
            and Northgate stations, respectively. As we touched upon in
            our gradient section, these stations are predisposed to not
            having commercial presence (17 businesses by Northgate, 5 by
            UW), and instead see a large number of ridership volume for
            either park-and-ride transfers (Northgate) or collegiate
            communal use (UW). The reasoning speaks for itself: Not all
            transit stations are meant to be used as a commercial
            opportunity, so it's only natural that statistics
            incorporating such non-commercial stations will drag down
            correlation in a commercially-focused study.

            The last notable standout is SODO station, which has low
            ridership volume but high business density. The explanation
            for this can also be tied back to the geographic factors
            explored in the gradient section: The industrial environment
            of the station reflects a high volume of businesses, but not
            the kind that attract foot traffic. The surrounding
            infrastructure supports automotive transport much more than
            pedestrians.
            """
        )

        st.markdown(
            """
            Probing into the relationship between station ridership and
            business density gave me an idea to further pit these
            variables against each other. Could visualizing the
            difference in variance between stations for these two
            variables give us more insights about their impact on shared
            correlation?
            """
        )

        # Graph 4: the same "density concentrates more than ridership"
        # point from the caption above Graph 3, but across the whole
        # sample rather than just the min/max extremes. Dot plot, not a
        # strip plot - simulated both first (see docs/DECISIONS.md): a strip
        # plot's jitter is random and carries no information of its own,
        # while a dot plot's stack height is a deterministic count a
        # reader can actually trust. "Businesses" is used as the category
        # label here, not "Density" - this section's
        # businesses_within_0_3mi is a raw count, not the gradient
        # section's businesses-per-square-mile density figure, and reusing
        # "density" for a different metric would blur two distinct numbers
        # this project has otherwise been careful to keep separate.
        cv_long = pd.concat([
            clean[["station", "businesses_within_0_3mi"]]
            .rename(columns={"businesses_within_0_3mi": "value"})
            .assign(metric="Businesses"),
            clean[["station", col]]
            .rename(columns={col: "value"})
            .assign(metric="Ridership"),
        ], ignore_index=True)
        cv_long["z"] = cv_long.groupby("metric")["value"].transform(
            lambda s: (s - s.mean()) / s.std()
        )
        cv_long["bin"] = (cv_long["z"] / 0.28).round() * 0.28
        cv_long = cv_long.sort_values(["metric", "bin", "z"])
        cv_long["stack_order"] = cv_long.groupby(["metric", "bin"]).cumcount()
        # Pixel offset computed directly, not left to Vega-Lite's own
        # linear scale - the two rows stack to different depths (whichever
        # single bin has the most stations sharing it, per row), and each
        # row needs its own tallest stack's top dot landing exactly on
        # that row's own label rather than sharing one scale across both.
        # scale=None on the encoding below passes these through as literal
        # pixel offsets instead of re-scaling them.
        DOT_SPACING_PX = 14
        row_max_stack = cv_long.groupby("metric")["stack_order"].transform("max")
        cv_long["offset_px"] = (row_max_stack - cv_long["stack_order"]) * DOT_SPACING_PX

        st.markdown(
            "**Graph 4: Dot Plot of Per-Station Ridership/Business "
            "Density Variance**"
        )
        with st.popover("How to read this chart"):
            st.markdown(
                "Each dot is one of the sixteen stations. The x-axis "
                "measures how far that station's value sits from the "
                "average for its own metric, in standard deviations - "
                "a rough gauge of \"typical\" (near 0, the middle) "
                "versus \"unusually high or low\" (far from 0) for that "
                "metric specifically. When several stations land close "
                "to the same value, their dots stack vertically "
                "instead of overlapping, so a tall stack means many "
                "stations cluster there, and a lone dot far out means "
                "that station is a real outlier, not just noise."
            )
        dot_chart = (
            alt.Chart(cv_long)
            .mark_circle(opacity=0.85, size=90)
            .encode(
                x=alt.X(
                    "bin:Q",
                    title="Standard deviations from mean",
                    # Explicit, 0.5-spaced values (Vega will just skip any
                    # outside the actual data range) - the default 0.2 step
                    # packed in enough ticks that Vega's own overlap-avoidance
                    # silently dropped every other label, and "0" (renamed
                    # "Mean" below) happened to land on a hidden one.
                    axis=alt.Axis(
                        values=[x / 2 for x in range(-8, 9)],
                        labelExpr="datum.value === 0 ? 'Mean' : datum.label",
                    ),
                ),
                y=alt.Y("metric:N", title=None),
                yOffset=alt.YOffset("offset_px:Q", scale=None),
                color=alt.Color(
                    "metric:N",
                    title=None,
                    legend=alt.Legend(orient="right"),
                    scale=alt.Scale(
                        domain=["Businesses", "Ridership"],
                        range=["#4c78a8", "#F2C94C"],
                    ),
                ),
                tooltip=[
                    alt.Tooltip("station:N", title="Station"),
                    alt.Tooltip("z:Q", title="SD from mean", format="+.2f"),
                ],
            )
            # Left padding reserved by hand. Vega autosizes the axis gutter
            # to 72px, but the "Businesses" label is 61px wide and sits at a
            # 16px offset from the axis, needing 77 - so its first character
            # was clipped off the left edge of the SVG ("Ridership", 51px,
            # cleared it and hid the bug). Measured in the rendered DOM, not
            # eyeballed; re-check if the category names change.
            .properties(
                height=320,
                padding={"left": 12, "top": 5, "right": 5, "bottom": 5},
            )
        )
        st.altair_chart(dot_chart, width="stretch")

        # Quick-glance insight for the chart itself: where's the biggest
        # single jump in each metric's sorted z-scores, and who sits past
        # it. Computed from cv_long, not hardcoded - finds the widest gap
        # between consecutive sorted stations per metric and names whoever
        # falls on the far side of it, so this stays accurate if the
        # underlying data changes rather than naming specific stations by
        # hand.
        def _biggest_gap(metric):
            g = cv_long[cv_long["metric"] == metric].sort_values("z").reset_index(drop=True)
            gaps = g["z"].diff()
            idx = gaps.idxmax()
            return gaps.max(), g.loc[idx:, "station"].tolist()

        biz_gap, biz_outliers = _biggest_gap("Businesses")
        rid_gap, rid_outliers = _biggest_gap("Ridership")
        st.caption(
            f"Most stations cluster similarly on both metrics. The "
            f"difference is in how far the tail sits past that cluster. "
            f"Businesses' widest gap is {biz_gap:.2f} SD, right before "
            f"{' and '.join(biz_outliers)}. Ridership's widest gap is "
            f"smaller ({rid_gap:.2f} SD, right before "
            f"{' and '.join(rid_outliers)}), consistent with its lower "
            "Coefficient of Variation (shown below in Table 3)."
        )

        st.markdown(
            """
            This dot plot provides a holistic view of the variance of the
            two variables explored in Graph 3 and Table 2 (business
            density per station and avg. monthly ridership per station).
            Their similar shapes are undermined by the larger gap between
            the aforementioned Westlake outlier/sister station Symphony
            and the rest of the pack in business density. The two
            downtown stations sit roughly two standard deviations away
            from the average, while the rest are within one.

            On the other hand, the ridership volume side is saved from a
            similar fate thanks to the smoother tail, particularly U
            District station sitting in what would otherwise be a large
            gap. Despite the
            improvement, each of the top three stations sits at least 0.5
            standard deviations above the one immediately below it, which
            is still significant.

            It's quite likely that by removing outliers, the variance in
            this section could be toned down, but as Graph 3's caption
            indicates, removing an outlier like Westlake also decreases
            the strength of the correlation. That being said, the
            coexistence of outliers and tight groups alike in Graph 4, as
            well as Graph 3, supports the medium-strong r-value from the
            beginning of this section.
            """
        )

        cv_table = (
            cv_long.groupby("metric")["value"]
            .agg(["mean", "std"])
            .assign(cv=lambda d: d["std"] / d["mean"])
            .rename(columns={"mean": "Mean", "std": "Std. Dev.", "cv": "CV"})
            .reset_index()
            .rename(columns={"metric": "Metric"})
        )
        with st.expander(
            "Table 3: Coefficient of Variation for Station Business "
            "Density and Ridership"
        ):
            st.dataframe(
                cv_table.style.format(
                    {"Mean": "{:,.1f}", "Std. Dev.": "{:,.1f}", "CV": "{:.3f}"}
                ),
                width="stretch",
                hide_index=True,
            )
        # Quick-glance insight for the table: the CV ratio itself, spelled
        # out as a plain multiple rather than requiring the reader to
        # divide the two CV values themselves.
        cv_ratio = cv_table.set_index("Metric").loc["Businesses", "CV"] / (
            cv_table.set_index("Metric").loc["Ridership", "CV"]
        )
        st.caption(
            f"Businesses' CV is {cv_ratio:.1f}x Ridership's. Businesses "
            "proportionally cluster far more unevenly across these "
            "sixteen stations than ridership does."
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

st.divider()
st.header("Chain Analysis")

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
        if len(chains) else "N/A",
    )

    with st.expander("Table 4: Brands with High Concentration near Link Stations"):
        chains_display = chains.head(25).rename(columns={
            "brand": "Brand Name",
            "station_count": "# of Stations within Proximity",
            "location_count": "# of Locations within Station Proximity",
        })
        st.dataframe(chains_display, width="stretch", hide_index=True)

    st.markdown(
        """
        One good way to tell if your commercial insight holds weight is to
        see if the big players in the market are supporting it. To that
        end, I sought to measure the share of chain locations in the
        transit-proximal commercial density of Seattle as part of this
        project. I figured if corporations that could establish multiple
        locations with relative ease played into the transit market, that
        could back my hypothesis with the actions of real-world decision
        makers.

        The initial data probe revealed promising results: 152 brands had
        at least two locations within the sample range of Seattle
        stations, with all chain brands accounting for 8.5% of total
        businesses in the corridor. Topping the line of individual brands
        angling toward transit is Subway, which is currently operating
        seven locations within a range of eight stations. The other 24
        brands listed in Table 4 also have noteworthy presences in the
        transit corridor, suggesting at least a share of the corporate
        market sees potential commercial value in transit-adjacent
        storefronts. Those positive points aside, the real test as to
        whether chain density is correlated with station proximity needs
        further validation against the concentric ring model.
        """
    )

    if CHAIN_RING_STATS_CSV.exists():
        chain_ring = pd.read_csv(CHAIN_RING_STATS_CSV)
        # Same ring_number_map/numbered_ring_labels built for Graph 1/2
        # above - reused here for the same "Ring N: <range>" labeling.
        chain_ring = chain_ring.assign(
            ring_label=lambda d: d["ring"].map(ring_number_map),
            chain_share_pct=lambda d: d["chain_share"] * 100,
        )

        chart_col, schematic_col = st.columns([3, 1])

        with chart_col:
            st.markdown("**Graph 5: Chain Share by Concentric Ring**")
            chain_ring_chart = (
                alt.Chart(chain_ring)
                .mark_bar()
                .encode(
                    x=alt.X(
                        "ring_label:N",
                        sort=numbered_ring_labels,
                        title="Concentric Ring",
                        axis=alt.Axis(labelAngle=0, labelExpr="split(datum.label, ': ')[0]"),
                    ),
                    y=alt.Y(
                        "chain_share_pct:Q",
                        title="Chain share of total business counts",
                        axis=alt.Axis(labelExpr="datum.label + '%'"),
                    ),
                    color=alt.Color(
                        "ring_label:N",
                        sort=numbered_ring_labels,
                        scale=alt.Scale(domain=numbered_ring_labels, range=ring_colors),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("ring_label:N", title="Ring"),
                        alt.Tooltip("chain_share_pct:Q", title="Chain share", format=".1f"),
                        alt.Tooltip("chain_matches:Q", title="Chain locations", format=","),
                        alt.Tooltip("total_matches:Q", title="Total businesses", format=","),
                    ],
                )
            )
            st.altair_chart(chain_ring_chart, width="stretch")

        with schematic_col:
            st.markdown(RING_SCHEMATIC_SVG, unsafe_allow_html=True)

        # Ties this chart's own small ring-3-to-4 reversal (8.3% -> 8.5%) to
        # the density gradient's already-documented ring-2-to-3 reversal
        # above (Table 1's "Ring 3 uptick, broken down") - both are outer-
        # ring upticks in what would otherwise be a clean decline, and both
        # trace back to stations from that same against-the-pattern group.
        # Verified against the pipeline's own joined business-ring data (not
        # the aggregate chain_ring_stats.csv alone, which can't isolate
        # individual stations): of that group, SODO and Stadium specifically
        # drive this one - Stadium's ring 4 (0.3-0.6mi) carries 31 chain
        # matches out of 373 businesses, largely borrowed from International
        # District/Chinatown per the existing "largely borrowed" finding in
        # docs/DECISIONS.md; SODO's ring 4 carries 18 of 149, consistent with its
        # own "real commerce only appearing toward Pioneer Square at the
        # buffer's edge" finding. Removing just those two stations turns the
        # aggregate ring-3-to-4 move back into a clean decline (8.7% -> 8.4%).
        st.caption(
            "Chain share's small reversal at the last ring (8.3% to 8.5%) "
            "traces to SODO and Stadium, the same against-the-pattern "
            "stations from Table 1's ring-3 breakdown, whose fourth ring "
            "reaches into Chinatown-International District and Pioneer "
            "Square. Removing them restores a clean decline (8.7% to "
            "8.4%): the same outer-ring, neighbor-sampling effect as the "
            "density gradient's ring-3 reversal, one ring further out."
        )

    st.markdown(
        """
        Graph 5 cleanly supports the hypothesis that chain share rises
        closer to the station, going from 11% share within concentric ring
        1 down to 8.5% within ring 4. On the micro-level, we see a similar
        unexpected rise in graph 1, though this time the discrepancy is
        from ring 3 to 4 (+0.2%). The caption underneath graph 5 connects
        this exception to the downtown overlap buffers that conflated some
        values in the gradient section.
        """
    )

    if CHAIN_RING_STATS_CSV.exists():
        with st.expander("Table 5: Chain Share Detail by Concentric Ring"):
            chain_ring_table = chain_ring.rename(columns={
                "ring_label": "Ring",
                "total_matches": "Total Businesses",
                "chain_matches": "Chain Locations",
                "chain_share": "Chain Share",
            })[["Ring", "Total Businesses", "Chain Locations", "Chain Share"]]
            st.dataframe(
                chain_ring_table.style.format({
                    "Total Businesses": "{:,.0f}",
                    "Chain Locations": "{:,.0f}",
                    "Chain Share": "{:.1%}",
                }),
                width="stretch",
                hide_index=True,
            )
else:
    st.info("Run `python src/step4_rings.py` to generate chain statistics.")

st.divider()
st.header("In Summary")

st.markdown(
    """
    Commercial density, ridership, and chain share all point the same way.
    Commercial density falls 62.9% from the first ring to the last,
    ridership correlates with that commercial density at r = 0.684, and
    even chains lean into platform proximity nearly as hard as independent
    businesses do. Three separate measures agreeing is a stronger claim
    than any one alone. Locational choice near public transit is a real,
    corridor-wide advantage for a Seattle business, not a marginal one.

    The same two complications explain most of the exceptions across all
    three analyses. Downtown buffer overlap double-counts businesses near
    Westlake, Symphony, and Pioneer Square across overlapping station
    rings, inflating outer-ring figures in the commercial density
    gradient, the chain-share reversal, and several ridership outliers
    alike. Per-station geography, industrial land at SODO and Stadium,
    parks and campus land elsewhere, adds further noise station by
    station. Neither complication undermines the overall pattern, but
    both cap how precisely any single station's figures should be read.
    """
)
