"""Step 5 - Render the heatmap to a standalone HTML file.

Input:  data/processed/stations.csv
        data/processed/businesses_geocoded.csv
Output: outputs/heatmap.html

The saved file is self-contained: it opens in any browser and embeds in
Streamlit. It is the project's visual anchor.

The heat layer is a Leaflet visual blur, not a statistical density estimate:
its radius is a rendering choice, not a bandwidth. The map is illustration;
the ring statistics from step 4 carry the quantitative claims.

Run:  python src/step5_map.py
"""

import re
import sys
import zipfile
from pathlib import Path

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
from folium.plugins import HeatMap, FastMarkerCluster
from jinja2 import Template

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    RIDERSHIP_CSV,
    HEATMAP_HTML,
    CITYWIDE_COVERAGE_CSV,
    CRS_GEOGRAPHIC,
    CRS_PROJECTED,
    RING_EDGES_METERS,
    RING_LABELS,
)

SEATTLE_CENTER = [47.6062, -122.3321]

GTFS_ZIP = DATA_RAW / "gtfs.zip"
# route_id 100479 is the 1 Line (exact route_short_name match; see
# step1_stations.py for why substring matching picks up a shuttle
# bus-bridge route). N23:S07 is its most-used shape (2,815 of 5,404 trips):
# one full-line direction, not a short-turn variant. The two directions are
# near-mirror images, so either would do.
RAIL_LINE_SHAPE_ID = "N23:S07"

# Heat layer tuning: Leaflet.heat pixel-space params, not a statistical
# bandwidth. Chosen by eye for legibility at the default city-wide zoom,
# where radius=12/blur=18 read as one undifferentiated wash. These tighter
# values keep neighborhood clusters distinct there and still work zoomed
# into downtown.
HEAT_RADIUS = 8
HEAT_BLUR = 10
HEAT_MIN_OPACITY = 0.35

# Replaces a pin's name where that name is the registrant's own identity
# rather than a chosen trade name. It states the reason so it reads as a
# deliberate omission, not missing data; the tooltip renders it in italics
# for the same reason. See the withholding block in main().
WITHHELD_NAME = "Name withheld (sole proprietor)"

# Single-hue orange ramp, pale at low density to deep at peak, so the scale
# reads as one color getting stronger. Leaflet.heat's default blue-to-red
# ramp shows most typical densities as blue/cyan, which reads as cold rather
# than low-but-nonzero. Based on Schematic 1 and the Findings page ring
# bars, one step more saturated at the low end (the palest peach was nearly
# invisible on light OSM tiles, since Leaflet.heat opacity follows density)
# plus a deeper #8F3A05 peak.
HEAT_GRADIENT = {0.3: "#FBB878", 0.5: "#F97316", 0.7: "#DE6412", 0.85: "#C0570F", 1.0: "#8F3A05"}

# The three groups config.py's NAICS_STOREFRONT_PREFIXES defines (retail,
# food service, personal services). Every kept business falls into exactly
# one, so no "Other" group is needed. Blue and aqua come from the Cove
# categorical palette, chosen for mutual distinguishability.
#
# Food service is magenta, not that palette's orange (#eb6834): 6 degrees of
# hue from the orange heat ramp, the orange pins sank into the densest
# areas, where food service matters most. Magenta sits 47 degrees off the
# ramp, 123 from the retail blue and 177 from the personal-services aqua.
# Violet separated better from the heat but sat only 43 degrees from the
# retail blue, and the two read alike at cluster size. Plum also lost to
# magenta by eye.
#
# name / prefixes / color. Labels spell out "NAICS Code:" rather than
# putting digits in parens, so the code isn't mistaken for the business
# count in parens (e.g. "(5,221)") beside it in the layer control.
NAICS_GROUPS = [
    ("Retail", ("44", "45"), "#2a78d6"),
    ("Food service", ("722",), "#C2185B"),
    ("Personal services", ("812",), "#1baf7a"),
]

# Finer, toggleable splits within each broad group: the top few specific
# NAICS codes by count, plus an "Other" residual for the rest of the group.
# Same color as the parent group: these layers filter which businesses of a
# color show without adding colors, so the 3-row legend still covers
# everything. Names and codes come from the actual data.
NAICS_SUBCATEGORIES = {
    "Retail": [
        ("Clothing & accessories", "458110"),
        ("Supermarkets & grocery", "445110"),
        ("All other misc. retailers (NAICS 459999)", "459999"),
    ],
    "Food service": [
        ("Full-service restaurants", "722511"),
        ("Limited-service restaurants", "722513"),
        ("Mobile food services", "722330"),
    ],
    "Personal services": [
        ("Beauty salons", "812112"),
        ("Pet care", "812910"),
        ("Barber shops", "812111"),
    ],
}


def naics_label(name: str, prefixes: tuple) -> str:
    return f"{name} — NAICS Code: {'/'.join(prefixes)}"

LEGEND_HTML = """
<div class="map-legend" style="
    position: fixed; bottom: 24px; right: 24px; z-index: 9999;
    background: white; padding: 10px 14px; border: 1px solid #999;
    border-radius: 4px; font-family: sans-serif; font-size: 13px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
">
  <div style="font-weight: bold; margin-bottom: 6px;">Business Category</div>
  {rows}
</div>
"""
LEGEND_ROW = """
  <div style="display:flex; align-items:center; margin:3px 0;">
    <span style="display:inline-block; width:11px; height:11px;
      border-radius:50%; background:{color}; margin-right:7px;
      border:1px solid rgba(0,0,0,0.3);"></span>{label}
  </div>
"""


def naics_group(code: str):
    code = str(code)
    for name, prefixes, color in NAICS_GROUPS:
        if code.startswith(prefixes):
            return name, color
    return None, None


def load_rail_line_shape():
    """Return the 1 Line's route geometry from GTFS shapes.txt.

    This is the actual rail alignment, curves included, not straight lines
    between stations.
    """
    if not GTFS_ZIP.exists():
        print(f"No GTFS feed at {GTFS_ZIP} - skipping the rail line layer.")
        return None
    with zipfile.ZipFile(GTFS_ZIP) as z, z.open("shapes.txt") as f:
        shapes = pd.read_csv(f, dtype=str)
    pts = shapes[shapes["shape_id"] == RAIL_LINE_SHAPE_ID].copy()
    if pts.empty:
        print(f"WARNING: shape_id {RAIL_LINE_SHAPE_ID!r} not in this GTFS feed - "
              "check trips.txt for route 100479's current most-used shape_id.")
        return None
    pts["shape_pt_sequence"] = pts["shape_pt_sequence"].astype(int)
    pts = pts.sort_values("shape_pt_sequence")
    return list(zip(pts["shape_pt_lat"].astype(float), pts["shape_pt_lon"].astype(float)))


def nearest_station_and_ring(businesses: pd.DataFrame, stations: pd.DataFrame):
    """Return each business's nearest station and its ring band for that station.

    Distance is straight-line, in projected meters. Deliberately separate
    from step4_rings.py's ring_stats, which assigns a business to every
    station whose buffer contains it (downtown overlap included, on purpose;
    see docs/DECISIONS.md). This is a single nearest-station view for the
    pin tooltip, not a re-derivation or replacement of the ring analysis.
    """
    biz_gdf = gpd.GeoDataFrame(
        businesses,
        geometry=gpd.points_from_xy(businesses["longitude"], businesses["latitude"]),
        crs=CRS_GEOGRAPHIC,
    ).to_crs(CRS_PROJECTED)
    sta_gdf = gpd.GeoDataFrame(
        stations,
        geometry=gpd.points_from_xy(stations["longitude"], stations["latitude"]),
        crs=CRS_GEOGRAPHIC,
    ).to_crs(CRS_PROJECTED)

    biz_xy = np.column_stack([biz_gdf.geometry.x, biz_gdf.geometry.y])
    sta_xy = np.column_stack([sta_gdf.geometry.x, sta_gdf.geometry.y])
    dist = np.sqrt(((biz_xy[:, None, :] - sta_xy[None, :, :]) ** 2).sum(axis=2))
    nearest_idx = dist.argmin(axis=1)
    nearest_dist = dist.min(axis=1)

    def band(d):
        for i, ring_label in enumerate(RING_LABELS):
            if RING_EDGES_METERS[i] <= d < RING_EDGES_METERS[i + 1]:
                return f"Ring {i + 1} ({ring_label})"
        outer_mi = RING_EDGES_METERS[-1] / 1609.344
        return f"Beyond ring 4 (>{outer_mi:.1f} mi)"

    nearest_station = sta_gdf["station"].to_numpy()[nearest_idx]
    ring_band = [band(d) for d in nearest_dist]
    return nearest_station, ring_band


def main():
    for path in (STATIONS_CSV, BUSINESSES_GEOCODED_CSV):
        if not path.exists():
            sys.exit(f"Missing {path}. Run the earlier steps first.")

    stations = pd.read_csv(STATIONS_CSV)
    businesses = pd.read_csv(BUSINESSES_GEOCODED_CSV, dtype={"naics": str})
    businesses = businesses.dropna(subset=["latitude", "longitude"])

    # `businesses` (all 11,409, citywide) stays the full set, the source for
    # the "all Seattle businesses" heat toggle. `businesses_in_rings` is the
    # subset within some station's outer ring (0.6 mi): the default view and
    # the source for every pin layer. Nearest-station distance replaces a
    # union-of-buffers computation: if the closest station is beyond the
    # outer ring edge, every other station is too, so the two conditions are
    # the same. The map opens ring-only because step4_rings.py's gradient and
    # chain analysis counts only ring-bounded businesses; opening citywide
    # would overstate how spread out the analysis's universe is.
    businesses["nearest_station"], businesses["ring_band"] = nearest_station_and_ring(
        businesses, stations
    )
    businesses_in_rings = businesses[
        ~businesses["ring_band"].str.startswith("Beyond")
    ].copy()
    print(f"{len(businesses) - len(businesses_in_rings):,} of {len(businesses):,} "
          f"businesses fall outside every station's ring "
          f"({len(businesses_in_rings):,} remain within a ring).")

    # Saved for the intro page's "citywide coverage" metric. Deliberately the
    # deduplicated nearest-station count, not step4_rings.py's business-ring
    # match count (6,847, which counts a business once per overlapping
    # station buffer): a business is either within walking distance of the
    # network or not, so a citywide coverage stat counts it once.
    pd.DataFrame([{
        "businesses_in_rings": len(businesses_in_rings),
        "businesses_citywide": len(businesses),
    }]).to_csv(CITYWIDE_COVERAGE_CSV, index=False)

    m = folium.Map(
        location=SEATTLE_CENTER,
        zoom_start=12,
        tiles=None,  # tiles added below, so their layer names can be set
        width=1000,
        height=650,
    )
    light_tiles = folium.TileLayer(
        tiles="OpenStreetMap",
        name="Light Mode",
        control=False,
    ).add_to(m)
    # Dark option: the same OSM tiles (no new provider or API key; see
    # docs/DECISIONS.md on why CartoDB was ruled out), recolored in the
    # browser by a CSS filter on this layer's tile container (class defined
    # below). Both base layers are control=False: a separate button near the
    # end of main() swaps them, so the layer control lists only overlays.
    # Overlays (rings, heat, pins) sit in other panes, untouched by the filter.
    dark_tiles = folium.TileLayer(
        tiles="OpenStreetMap",
        name="Dark Mode",
        class_name="dark-osm-tiles",
        show=False,
        control=False,
    ).add_to(m)

    # Two heat layers, same tuning, different universe. Within-rings is the
    # default, matching what the rest of the project analyzes (see
    # docs/DECISIONS.md). All-Seattle is an opt-in for citywide context, off
    # by default so the map opens on the same scope as the Findings page.
    HeatMap(
        businesses_in_rings[["latitude", "longitude"]].values.tolist(),
        radius=HEAT_RADIUS,
        blur=HEAT_BLUR,
        min_opacity=HEAT_MIN_OPACITY,
        gradient=HEAT_GRADIENT,
        name="Commercial Density (Within Station Proximity)",
        show=True,
    ).add_to(m)
    HeatMap(
        businesses[["latitude", "longitude"]].values.tolist(),
        radius=HEAT_RADIUS,
        blur=HEAT_BLUR,
        min_opacity=HEAT_MIN_OPACITY,
        gradient=HEAT_GRADIENT,
        name="Commercial Density (All Seattle Businesses)",
        show=False,
    ).add_to(m)

    # Ring circles, each toggleable, all on by default.
    for i, label in enumerate(RING_LABELS):
        layer = folium.FeatureGroup(name=f"Concentric Ring {i + 1}: {label}", show=True)
        for _, station in stations.iterrows():
            folium.Circle(
                location=[station["latitude"], station["longitude"]],
                radius=RING_EDGES_METERS[i + 1],
                color="#2c3e50",
                weight=1,
                fill=False,
                opacity=0.5,
            ).add_to(layer)
        layer.add_to(m)

    # --- The rail line itself: visual context, on by default ---
    # Added before the stations so the stations draw on top. SVG paths stack
    # in the order they are added; with the line on top, its 5px path
    # covered the centre of every station it passes through, and a tap or
    # hover there reached the line (which has no tooltip) instead of the
    # station. Measured 2026-10-03: 6 of 16 station centres were covered.
    rail_coords = load_rail_line_shape()
    if rail_coords:
        rail_layer = folium.FeatureGroup(name="Link 1 Line route", show=True, control=False)
        folium.PolyLine(
            rail_coords, color="#0a7a3c", weight=5, opacity=0.85,
        ).add_to(rail_layer)
        # A large, always-visible label, not a hover tooltip. Anchored at
        # Westlake's latitude (the downtown corridor) but offset west over
        # Elliott Bay/Myrtle Edwards Park, clear of the dense heat/pin
        # corridor and of the layer control. Anchors farther south landed
        # under the control panel.
        label_station = stations.loc[stations["station"] == "Westlake"].iloc[0]
        label_lat = label_station["latitude"]
        label_lon = label_station["longitude"] - 0.045
        folium.Marker(
            location=[label_lat, label_lon],
            icon=folium.DivIcon(html="""
                <div style="
                    font-size: 22px; font-weight: bold; color: #0a7a3c;
                    text-shadow: -1px -1px 0 #fff, 1px -1px 0 #fff,
                                 -1px 1px 0 #fff, 1px 1px 0 #fff,
                                 0 0 6px #fff;
                    white-space: nowrap; pointer-events: none;
                ">1 Line</div>
            """),
        ).add_to(rail_layer)
        rail_layer.add_to(m)

    # Ridership is the 2025 average of monthly totals (see docs/DECISIONS.md
    # for why that metric, not "average weekday boardings"). Left join, not
    # inner: a station missing from the CSV keeps its marker, without a
    # ridership figure, rather than vanishing silently.
    if RIDERSHIP_CSV.exists():
        ridership = pd.read_csv(RIDERSHIP_CSV)
        stations = stations.merge(ridership, on="station", how="left")
        no_ridership = stations["avg_monthly_boardings"].isna().sum()
        if no_ridership:
            print(f"WARNING: {no_ridership} station(s) have no ridership match - "
                  "station names must agree between stations.csv and ridership_by_station.csv")
    else:
        stations["avg_monthly_boardings"] = None
        print(f"No ridership file at {RIDERSHIP_CSV} - station tooltips will omit it.")

    # control=False: always on, with no layer-control entry. Same as the rail
    # line above; both are baseline map context, not optional data layers.
    station_layer = folium.FeatureGroup(name="Stations", control=False)
    for _, station in stations.iterrows():
        boardings = station["avg_monthly_boardings"]
        # Label first, value second, matching the business tooltip's
        # "NAICS code: 722513". Spells out "average of monthly totals"
        # because the metric is deliberately not average weekday or daily
        # boardings (see docs/DECISIONS.md), and a shorter label would be
        # ambiguous between them.
        ridership_line = (
            f"Avg. monthly boardings (2025 avg. of monthly totals): {boardings:,.0f}"
            if pd.notna(boardings) else "No ridership data"
        )
        tooltip_html = f"<b>{station['station']}</b><br>{ridership_line}"
        folium.CircleMarker(
            location=[station["latitude"], station["longitude"]],
            radius=5,
            color="#1a5490",
            fill=True,
            fill_opacity=0.9,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(station_layer)
    station_layer.add_to(m)

    # --- Individual business pins, one clustered layer per NAICS group ----
    # Even after the ring filter, plain (unclustered) markers would overlap
    # unreadably at any practical zoom and make a much heavier file.
    # FastMarkerCluster ships a compact coordinate array and clusters
    # client-side instead of one full Marker object per point. The three
    # broad NAICS-group layers are on by default; the finer subcategory
    # splits stay off as a detail view.
    #
    # Pins stay ring-only even though the heat layer has an all-Seattle
    # toggle: doubling all 15 pin layers would double an already long layer
    # control, for businesses outside the analysis scope. The heat toggle
    # covers citywide context on its own.
    #
    # nearest_station / ring_band (used for the hover tooltip) were computed
    # above on the full pre-filter set, for the ring filter. See
    # nearest_station_and_ring() for why this is separate from step4's
    # overlap-aware ring_stats.
    businesses_in_rings["_group"], businesses_in_rings["_color"] = zip(
        *businesses_in_rings["naics"].map(naics_group)
    )
    unmatched = businesses_in_rings["_group"].isna().sum()
    if unmatched:
        print(f"WARNING: {unmatched} businesses matched no NAICS group - "
              "check NAICS_GROUPS against NAICS_STOREFRONT_PREFIXES in config.py")

    # --- Withhold names that are a person's own identity -------------------
    # A trade name chosen for a shop is commercial information, and mapping it
    # is the point of this project. A sole proprietor's own name is not, and
    # this registry publishes one wherever no trade name was filed.
    #
    # The test: the published name IS the legal entity name (a chosen trade
    # name gives two different strings) AND the entity is a natural person
    # rather than a company. The second half is load-bearing: without it,
    # single-member LLCs dominate, because an LLC's legal name is its brand
    # ("Barking Gorgeous LLC"). An LLC filed under the owner's own name is
    # deliberately not caught; that is a commercial identity chosen at filing.
    #
    # Substituted HERE, where the pin arrays are built, not in the tooltip
    # JavaScript: the pin data is baked into heatmap.html as a literal array,
    # so hiding a name only at render time would leave it readable in the
    # page source. It must never enter the file.
    #
    # Cost: roughly three dozen pins whose trade name equals their legal name
    # ("Hami Salon") lose their label. Accepted, because the rule recomputes
    # from the registry on every run, unlike a hand-maintained list that
    # would go stale silently against a newer export.
    # See scripts/check_personal_exposure.py and the Methodology page.
    def _entity_key(name):
        if not isinstance(name, str):
            return ""
        s = re.sub(r"[^A-Z0-9 ]", " ", name.upper())
        s = re.sub(r"\b(?:LLC|INC|CORP|CO|LTD|LP|LLP|PLLC|THE)\b", " ", s)
        return " ".join(s.split())

    _published = businesses_in_rings["business_name"].map(_entity_key)
    _legal = businesses_in_rings.get(
        "Business Legal Name", pd.Series("", index=businesses_in_rings.index)
    ).map(_entity_key)
    _is_person = (
        businesses_in_rings.get(
            "Ownership Type", pd.Series("", index=businesses_in_rings.index)
        ).fillna("").str.strip() == "Sole proprietorship"
    )
    _withhold = (_published != "") & (_published == _legal) & _is_person
    if _withhold.any():
        businesses_in_rings.loc[_withhold, "business_name"] = WITHHELD_NAME
        print(f"{_withhold.sum()} pin name(s) withheld as a registrant's own "
              "identity (see scripts/check_personal_exposure.py)")

    def add_pin_layer(rows, sublabel, group_name, color, bold=False, show=False):
        """Add one toggleable, clustered, colored pin layer to the map.

        Used for every business layer, broad or fine-grained. bold=True marks
        a whole-NAICS-group layer in the layer control, setting it apart from
        the finer splits; Leaflet renders layer names as HTML, so a literal
        <b> tag is enough. The three bold group layers are the only pin
        layers on by default (show=True)."""
        data = [
            [row.latitude, row.longitude, row.business_name, row.naics,
             row.nearest_station, row.ring_band]
            for row in rows.itertuples()
        ]
        if not data:
            return
        callback = f"""
            function (row) {{
                // business_name is free text from the City's license
                // registry; a name containing '&' or '<' ("Smith & Sons")
                // would otherwise break the tooltip HTML or inject markup.
                // The other fields are computed values, not at risk.
                function esc(s) {{
                    return String(s).replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;').replace(/>/g, '&gt;');
                }}
                var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {{
                    radius: 5, color: '{color}', fillColor: '{color}',
                    fillOpacity: 0.85, weight: 1
                }});
                // Withheld names render italic rather than bold, so they read
                // as a label rather than as a business actually called that.
                var name = esc(row[2]);
                var head = row[2] === {WITHHELD_NAME!r}
                    ? '<i>' + name + '</i>'
                    : '<b>' + name + '</b>';
                var html = head + '<br>' +
                    'NAICS code: ' + row[3] + '<br>' +
                    'Nearest station: ' + row[4] + '<br>' +
                    row[5];
                marker.bindTooltip(html, {{sticky: true}});
                return marker;
            }}
        """
        # Leaflet.markercluster's default iconCreateFunction gives every
        # cluster the same 40x40px icon, so a 2-point cluster has as large a
        # hit area as a 500-point one. Near the zoom where a cluster splits,
        # that oversized hit area covers and blocks hovering on an adjacent
        # lone pin. Scaling icon size (and hit area) with count fixes this at
        # the source; tuning cluster radius or zoom thresholds would only
        # make the collision less likely.
        icon_create_function = f"""
            function (cluster) {{
                var count = cluster.getChildCount();
                var size = count <= 3 ? 18 : count <= 10 ? 26 : count <= 50 ? 34 : 42;
                var fontSize = Math.max(9, Math.round(size * 0.42));
                return new L.DivIcon({{
                    html: '<div style="width:100%; height:100%; border-radius:50%; ' +
                        'background:{color}; opacity:0.85; ' +
                        'border:1px solid rgba(0,0,0,0.4); display:flex; ' +
                        'align-items:center; justify-content:center; color:#fff; ' +
                        'font-size:' + fontSize + 'px; font-weight:600;">' +
                        count + '</div>',
                    className: 'business-cluster-icon',
                    iconSize: new L.Point(size, size)
                }});
            }}
        """
        # FastMarkerCluster's own `show` param doesn't reliably hide it at
        # load; a FeatureGroup wrapper (as the ring layers use) respects
        # show=False. The business count gets its own parens, separate from
        # any NAICS code in the label, so the two numbers aren't confused.
        layer_name = f"Businesses: {group_name} — {sublabel} ({len(data):,})"
        if bold:
            layer_name = f"<b>{layer_name}</b>"
        fg = folium.FeatureGroup(name=layer_name, show=show)
        FastMarkerCluster(
            data, callback=callback, icon_create_function=icon_create_function
        ).add_to(fg)
        fg.add_to(m)

    # Layer-control order: the three broad (bold) group layers first, then each
    # group's finer splits below them, still grouped by umbrella. Two loops
    # because Leaflet lists layers in the order they were added.
    for name, prefixes, color in NAICS_GROUPS:
        group_rows = businesses_in_rings[businesses_in_rings["_group"] == name]

        # The broad group as a whole, toggleable on its own. sublabel is
        # just the code, not naics_label(name, prefixes): add_pin_layer
        # already prefixes group_name, so the full label would repeat the
        # group name in the layer name.
        add_pin_layer(
            group_rows, f"NAICS Code: {'/'.join(prefixes)}", name, color, bold=True, show=True
        )

    for name, prefixes, color in NAICS_GROUPS:
        group_rows = businesses_in_rings[businesses_in_rings["_group"] == name]

        # Finer splits within the group: a few specific NAICS codes by
        # count, plus "Other" for the rest. Same color throughout; see the
        # NAICS_SUBCATEGORIES comment for why.
        named_codes = {code for _, code in NAICS_SUBCATEGORIES[name]}
        for sublabel, code in NAICS_SUBCATEGORIES[name]:
            add_pin_layer(group_rows[group_rows["naics"] == code], sublabel, name, color)
        other_rows = group_rows[~group_rows["naics"].isin(named_codes)]
        add_pin_layer(other_rows, "Other", name, color)

    m.get_root().html.add_child(folium.Element(
        LEGEND_HTML.format(rows="".join(
            LEGEND_ROW.format(color=color, label=naics_label(name, prefixes))
            for name, prefixes, color in NAICS_GROUPS
        ))
    ))

    # Collapsed by default: with every heat, ring and business layer listed,
    # an always-open panel covered much of the map. A nested "Businesses" group would need a custom Leaflet control or
    # a third-party plugin; this uses Leaflet's built-in collapsed state plus
    # a height cap, so even fully expanded the panel never covers the map.
    #
    # position="topleft", not Leaflet's topright default: the map's fixed
    # 1000px width (a Leaflet.heat init-race workaround) is often wider than
    # Streamlit's content area with the sidebar open, which pushes a topright
    # control past the visible edge. topleft stacks under the zoom control
    # and stays visible at any width, anchored to the map's origin corner.
    folium.LayerControl(collapsed=True, position="topleft").add_to(m)
    m.get_root().html.add_child(folium.Element("""
        <style>
            .leaflet-control-layers-expanded {
                max-height: 480px;
                overflow-y: auto;
            }
            /* Light/dark switch: one opaque 30x60 box (sun cell over moon
               cell) with a thumb behind the active mode - top in light, bottom
               in dark. Selectors carry .leaflet-touch to out-rank Leaflet's own
               30x30 .leaflet-bar a sizing. */
            .leaflet-touch .leaflet-bar a.mode-switch-btn,
            .leaflet-bar a.mode-switch-btn {
                position: relative;
                display: block;
                width: 30px;
                height: 60px;
                padding: 0;
                line-height: 0;
                border-bottom: none;
                overflow: hidden;
            }
            .mode-switch-btn .mode-thumb {
                position: absolute;
                left: 2px;
                top: 2px;
                width: 26px;
                height: 26px;
                border-radius: 3px;
                background: #C2500A;
                transition: transform 0.2s ease, background 0.2s ease;
            }
            .mode-switch-btn[data-mode="dark"] .mode-thumb {
                transform: translateY(30px);
                background: #FBB878;
            }
            .mode-switch-btn .mode-icon {
                position: absolute;
                left: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #6B6B6B;
            }
            .mode-switch-btn .mode-sun { top: 0; }
            .mode-switch-btn .mode-moon { top: 30px; }
            .mode-switch-btn .mode-icon svg {
                width: 16px;
                height: 16px;
                display: block;
            }
            .mode-switch-btn[data-mode="light"] .mode-sun { color: #FFFFFF; }
            .mode-switch-btn[data-mode="dark"] .mode-moon { color: #171412; }
            .dark-base .mode-switch-btn[data-mode="dark"] .mode-sun {
                color: #A39A90;
            }
            /* Invert flips OSM's light map to dark, hue-rotate(180deg) undoes
               the color swap (water stays blue-ish, not orange), and the
               brightness/saturate tweaks keep it from glaring. */
            .dark-osm-tiles {
                filter: invert(1) hue-rotate(180deg) brightness(0.85)
                        contrast(0.9) saturate(0.7);
            }
            /* Everything below applies only while Dark Mode is selected (the
               class sits on <body> so the legend, which lives outside the
               Leaflet container, is covered too). Colors match the site's
               warm charcoal theme. !important on the legend because its
               light styling is inline. */
            .dark-base { background: #171412; }
            /* Ring outlines are dark slate (#2c3e50, used nowhere else) -
               invisible on a dark base, so lighten them. */
            .dark-base path.leaflet-interactive[stroke="#2c3e50"] {
                stroke: #d9d2ca;
            }
            .dark-base .map-legend {
                background: #221D19 !important;
                color: #F3EDE6 !important;
                border-color: #3A322B !important;
            }
            /* border-color only: keeping Leaflet's own border width means the
               controls don't shift by a pixel when the mode changes. */
            .dark-base .leaflet-bar,
            .dark-base .leaflet-control-layers {
                border-color: #3A322B;
                box-shadow: none;
            }
            .dark-base .leaflet-bar a,
            .dark-base .leaflet-control-layers {
                background-color: #221D19;
                color: #F3EDE6;
            }
            .dark-base .leaflet-bar a { border-bottom-color: #3A322B; }
            .dark-base .leaflet-bar a:hover,
            .dark-base .leaflet-bar a:focus {
                background-color: #2A231E;
            }
            .dark-base .leaflet-bar a.leaflet-disabled {
                background-color: #1D1916;
                color: #6B6259;
            }
            /* The layer-control icon is a dark-on-white image; invert it. */
            .dark-base .leaflet-control-layers-toggle { filter: invert(1); }
            .dark-base .leaflet-control-layers-expanded { color-scheme: dark; }
            .dark-base .leaflet-control-layers-separator {
                border-top-color: #3A322B;
            }
            .dark-base .leaflet-control-attribution {
                background: rgba(23, 20, 18, 0.8);
                color: #A39A90;
            }
            .dark-base .leaflet-control-attribution a { color: #FBB878; }
            /* Pin hover tooltip (Leaflet's own white box) and its arrow. */
            .dark-base .leaflet-tooltip {
                background: #221D19;
                color: #F3EDE6;
                border-color: #3A322B;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
            }
            .dark-base .leaflet-tooltip-top:before { border-top-color: #3A322B; }
            .dark-base .leaflet-tooltip-bottom:before { border-bottom-color: #3A322B; }
            .dark-base .leaflet-tooltip-left:before { border-left-color: #3A322B; }
            .dark-base .leaflet-tooltip-right:before { border-right-color: #3A322B; }
        </style>
    """))
    # Light/dark button, top-left under the layer control (Leaflet stacks
    # topleft controls in the order added, and this follows LayerControl).
    # Top-left for the same reason as the layer control: at the fixed 1000px
    # width a top-right button can sit past the visible edge. It swaps the
    # two base layers and puts a `dark-base` class on <body> so the CSS above
    # can restyle overlays and controls (body, not the map container, so the
    # legend outside the container is covered too). The map opens on the
    # visitor's prefers-color-scheme and follows OS changes until the switch
    # is used; nothing is stored, so a reload goes back to following the
    # system. A MacroElement rather than a bare script Element: it renders
    # after the map variable exists (a bare one lands above it and throws).
    mode_toggle = folium.MacroElement()
    mode_toggle.light_tiles = light_tiles
    mode_toggle.dark_tiles = dark_tiles
    mode_toggle._template = Template("""
        {% macro script(this, kwargs) %}
            (function () {
                var map = {{ this._parent.get_name() }};
                var light = {{ this.light_tiles.get_name() }};
                var dark = {{ this.dark_tiles.get_name() }};
                var svg = '<svg viewBox="0 0 24 24" fill="none" ' +
                    'stroke="currentColor" stroke-width="2" ' +
                    'stroke-linecap="round" stroke-linejoin="round" ' +
                    'aria-hidden="true">';
                var MOON = svg + '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
                var SUN = svg + '<circle cx="12" cy="12" r="4"/>' +
                    '<path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4' +
                    'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
                var ModeControl = L.Control.extend({
                    options: {position: 'topleft'},
                    onAdd: function () {
                        // A two-position switch: sun (top) and moon (bottom)
                        // are always both shown, and a thumb sits behind
                        // whichever mode is active.
                        var bar = L.DomUtil.create('div', 'leaflet-bar leaflet-control mode-switch');
                        var btn = L.DomUtil.create('a', 'mode-switch-btn', bar);
                        btn.href = '#';
                        btn.setAttribute('role', 'switch');
                        btn.setAttribute('aria-label', 'Dark mode');
                        btn.innerHTML = '<span class="mode-thumb"></span>' +
                            '<span class="mode-icon mode-sun">' + SUN + '</span>' +
                            '<span class="mode-icon mode-moon">' + MOON + '</span>';
                        function setMode(isDark) {
                            if (isDark) {
                                map.addLayer(dark);
                                map.removeLayer(light);
                            } else {
                                map.addLayer(light);
                                map.removeLayer(dark);
                            }
                            document.body.classList.toggle('dark-base', isDark);
                            btn.setAttribute('data-mode', isDark ? 'dark' : 'light');
                            btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
                            btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
                        }

                        // Start on the OS/browser setting rather than always
                        // light; prefers-color-scheme resolves inside this
                        // iframe as it would top-level. Once the switch is
                        // used, that choice wins until reload, so an OS
                        // auto-switch at sunset can't undo a deliberate click.
                        var mq = window.matchMedia
                            ? window.matchMedia('(prefers-color-scheme: dark)')
                            : null;
                        var manual = false;
                        setMode(!!(mq && mq.matches));
                        if (mq) {
                            var onSystemChange = function (e) {
                                if (!manual) setMode(e.matches);
                            };
                            if (mq.addEventListener) {
                                mq.addEventListener('change', onSystemChange);
                            } else if (mq.addListener) {
                                mq.addListener(onSystemChange);  // older Safari
                            }
                        }

                        function toggle() {
                            manual = true;
                            setMode(!map.hasLayer(dark));
                        }
                        L.DomEvent.disableClickPropagation(bar);
                        L.DomEvent.on(btn, 'click', function (e) {
                            L.DomEvent.preventDefault(e);
                            toggle();
                        });
                        L.DomEvent.on(btn, 'keydown', function (e) {
                            if (e.key === ' ') {
                                L.DomEvent.preventDefault(e);
                                toggle();
                            }
                        });
                        return bar;
                    }
                });
                new ModeControl().addTo(map);
            })();
        {% endmacro %}
    """)
    m.add_child(mode_toggle)

    # --- Phones: open on the centre, and taps that reach their target --------
    # On a phone, Streamlit narrows the map's frame to the screen (343px on a
    # 375px phone) while the map inside stays 1000px wide, so only its left
    # edge shows: the map opened on Elliott Bay with every station off to the
    # right. Panning by half the hidden width puts the original centre in
    # the middle of the visible window. The 1000px width itself stays.
    #
    # Touch screens get a tap resolver in place of tooltips, adapted from the
    # sister project's measured fix (2026-10-03). Measured here before it, in
    # a 343x650 frame: an 11px dot opened only on a dead-centre tap in
    # WebKit-style (no snapping) taps; a dot inside a spiderfied group never
    # opened on the second tap, because the dot's click bubbled to the map and
    # markercluster collapses the group on any map click; 22 of 45 tooltips ran
    # past the frame edge. The resolver catches each tap before Leaflet, picks
    # the nearest dot, station or cluster within REACH of where the finger
    # lifted, stops the click for a dot or station (so the group stays open)
    # and shows that layer's own tooltip content in a fixed panel. Inert unless
    # (pointer: coarse) matches, so desktop keeps its hover tooltips. Panel
    # content is the tooltip text built above, withheld names included, so it
    # exposes nothing new. See docs/DECISIONS.md.
    m.get_root().html.add_child(folium.Element("""
        <style>
            .tap-panel {
                display: none; position: fixed; z-index: 10000; box-sizing: border-box;
                left: 10px; bottom: 24px; max-width: 420px; overflow-y: auto;
                padding: 8px 40px 8px 12px; border-radius: 4px; overflow-wrap: anywhere;
                font: 13px/1.4 sans-serif;
                background: #fff; color: #222; border: 1px solid #999;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
            }
            .tap-panel.shown { display: block; }
            .tap-close {
                position: absolute; top: 0; right: 0; width: 40px; height: 40px;
                padding: 0; border: 0; background: none; color: inherit; cursor: pointer;
                font: 22px/40px sans-serif;
            }
            .dark-base .tap-panel {
                background: #221D19; color: #F3EDE6; border-color: #3A322B;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
            }
            /* White inner ring, near-black outer ring: reads on light and dark tiles. */
            .tap-ring {
                box-sizing: border-box; border-radius: 50%; pointer-events: none;
                border: 2px solid #fff;
                box-shadow: 0 0 0 2px #111, 0 0 6px 2px rgba(0, 0, 0, 0.45);
            }
            /* The panel replaces tooltips on touch screens. */
            @media (pointer: coarse) { .leaflet-tooltip-pane { display: none; } }
        </style>
    """))
    touch = folium.MacroElement()
    touch._template = Template("""
        {% macro script(this, kwargs) %}
            (function () {
                var m = {{ this._parent.get_name() }};
                var REACH = 22;     // px from a centre: a 44px target (WCAG 2.5.5, Apple HIG)
                var TIE_PX = 2;     // edges this close tie, and a dot or station beats a cluster
                var ROOM_PX = 200;  // map height the panel needs above the legend
                var RING_PX = 26;   // the selection ring's outer diameter
                var LIFT_MS = 800;  // a click this soon after a touchend belongs to that tap

                m.whenReady(function () {
                    var vw = document.documentElement.clientWidth;
                    var hidden = m.getSize().x - vw;
                    if (vw > 0 && hidden > 0) m.panBy([hidden / 2, 0], {animate: false});
                });

                var el = m.getContainer();
                var mq = window.matchMedia ? window.matchMedia('(pointer: coarse)') : null;
                var legend = document.querySelector('.map-legend');

                var panel = document.createElement('div');
                panel.className = 'tap-panel';
                var body = document.createElement('div');
                body.setAttribute('role', 'status');
                body.setAttribute('aria-live', 'polite');
                var close = document.createElement('button');
                close.type = 'button';
                close.className = 'tap-close';
                close.setAttribute('aria-label', 'Close');
                close.innerHTML = '&times;';
                panel.appendChild(body);
                panel.appendChild(close);
                document.body.appendChild(panel);

                var ring = null, picked = null, passing = false;
                function follow() { if (ring && picked) { ring.setLatLng(picked.getLatLng()); place(); } }
                function clear() {
                    panel.classList.remove('shown');
                    panel.removeAttribute('data-for');
                    body.innerHTML = '';
                    if (ring) { m.removeLayer(ring); ring = null; }
                    if (picked) { picked.off('move', follow); picked = null; }
                }

                // Bottom-left of the visible part of the map, above the legend
                // when there is room, beside it otherwise; at the top, under
                // the controls, when it would cover the dot it describes.
                function place() {
                    if (!panel.classList.contains('shown')) return;
                    var c = el.getBoundingClientRect();
                    var vw = document.documentElement.clientWidth || window.innerWidth;
                    var vh = document.documentElement.clientHeight || window.innerHeight;
                    var top = Math.max(c.top, 0), bot = Math.min(c.bottom, vh);
                    var left = Math.max(c.left, 0) + 10, right = vw - Math.min(c.right, vw) + 10;
                    var bottom = vh - bot + 24;
                    var lg = legend ? legend.getBoundingClientRect() : null;
                    if (lg && lg.width && lg.left < vw - right && lg.top < bot - 24) {
                        if (lg.top - top >= ROOM_PX) bottom = Math.max(bottom, vh - lg.top + 8);
                        else right = Math.max(right, vw - lg.left + 8);
                    }
                    panel.style.left = left + 'px';
                    panel.style.right = right + 'px';
                    panel.style.top = 'auto';
                    panel.style.bottom = bottom + 'px';
                    panel.style.maxHeight = Math.max(80, Math.round(0.45 * (bot - top))) + 'px';
                    if (ring && ring._icon && overlaps(ring._icon.getBoundingClientRect(), panel.getBoundingClientRect())) {
                        var under = top, tl = el.querySelector('.leaflet-top.leaflet-left');
                        if (tl) under = Math.max(under, tl.getBoundingClientRect().bottom);
                        panel.style.bottom = 'auto';
                        panel.style.top = (under + 8) + 'px';
                        if (overlaps(ring._icon.getBoundingClientRect(), panel.getBoundingClientRect())) {
                            panel.style.top = 'auto';
                            panel.style.bottom = bottom + 'px';
                        }
                    }
                }
                function overlaps(a, b) {
                    return a.right + 8 > b.left && a.left - 8 < b.right && a.bottom + 8 > b.top && a.top - 8 < b.bottom;
                }
                window.addEventListener('resize', place);
                m.on('moveend', place);
                close.addEventListener('click', clear);
                document.addEventListener('keydown', function (e) { if (e.key === 'Escape') clear(); });

                function select(layer) {
                    var text = layer.getTooltip().getContent();
                    if (typeof text === 'function') text = text(layer);
                    if (picked !== layer) clear();
                    // The tooltip's own content, escaped when the pin was built.
                    if (typeof text === 'string') body.innerHTML = text;
                    else if (text && text.cloneNode) { body.innerHTML = ''; body.appendChild(text.cloneNode(true)); }
                    panel.setAttribute('data-for', String(L.stamp(layer)));
                    panel.classList.add('shown');
                    if (!ring) {
                        ring = L.marker(layer.getLatLng(), {
                            interactive: false, keyboard: false,
                            icon: L.divIcon({className: 'tap-ring', iconSize: [RING_PX, RING_PX]})
                        }).addTo(m);
                    }
                    if (picked !== layer) { picked = layer; layer.on('move', follow); }
                    place();
                    if (layer.isTooltipOpen()) layer.closeTooltip();
                }

                // Where the finger lifted. Chromium's touch adjustment moves a
                // tap's click onto a nearby target and reports the moved point;
                // the touch events keep the real one.
                var lift = null;
                el.addEventListener('touchend', function (e) {
                    var t = e.changedTouches && e.changedTouches[0];
                    lift = t ? {x: t.clientX, y: t.clientY, at: Date.now()} : null;
                }, {capture: true, passive: true});
                function tapPoint(e) {
                    if (lift && Date.now() - lift.at < LIFT_MS &&
                        Math.abs(lift.x - e.clientX) + Math.abs(lift.y - e.clientY) <= 2 * REACH) {
                        return m.mouseEventToContainerPoint({clientX: lift.x, clientY: lift.y});
                    }
                    return m.mouseEventToContainerPoint(e);
                }

                // The nearest dot, station or cluster within reach. The rail
                // line and ring outlines are not targets: neither has a tooltip.
                function nearest(p) {
                    var best = null, fanned = null;
                    function consider(kind, layer, d, reach, edge, rank) {
                        if (d > reach) return;
                        // Equal distance and kind: the later layer, drawn on top,
                        // wins (categories cluster separately, so badges can stack).
                        if (!best || edge < best.edge - TIE_PX ||
                            (edge <= best.edge + TIE_PX && rank < best.rank) ||
                            (rank === best.rank && Math.abs(edge - best.edge) < 0.5)) {
                            best = {kind: kind, layer: layer, edge: edge, rank: rank};
                        }
                        // A dot of a spiderfied group the reader just opened wins outright.
                        if (layer._spiderLeg && (!fanned || edge < fanned.edge)) {
                            fanned = {kind: kind, layer: layer, edge: edge, rank: rank};
                        }
                    }
                    m.eachLayer(function (l) {
                        var q, r, d;
                        if (l instanceof L.CircleMarker) {
                            // L.Circle (the rings, radius in meters) and markers
                            // without a tooltip are not targets.
                            if (l instanceof L.Circle || !l.getTooltip || !l.getTooltip() || !l._point) return;
                            q = m.latLngToContainerPoint(l.getLatLng());
                            r = l._radius + (l.options.stroke ? l.options.weight / 2 : 0);
                            d = q.distanceTo(p);
                            consider('point', l, d, Math.max(REACH, r), d - r, 0);
                        } else if (L.MarkerCluster && l instanceof L.MarkerCluster && l._icon) {
                            if (l._group && l._group._spiderfied === l) return;
                            q = m.latLngToContainerPoint(l.getLatLng());
                            r = l._icon.offsetWidth / 2;
                            d = q.distanceTo(p);
                            consider('cluster', l, d, Math.max(REACH, r), d - r, 1);
                        }
                    });
                    return fanned || best;
                }

                el.addEventListener('click', function (e) {
                    if (passing || !(mq && mq.matches)) return;
                    var t = e.target;
                    if (t && t.closest && t.closest('.leaflet-control')) return;
                    var best = nearest(tapPoint(e));
                    if (!best) { clear(); return; }
                    e.stopPropagation();
                    if (best.kind === 'point') { select(best.layer); return; }
                    // A cluster: re-send the click to its badge, so markercluster
                    // zooms or spiderfies exactly as for a direct tap.
                    clear();
                    passing = true;
                    try {
                        best.layer._icon.dispatchEvent(new MouseEvent('click', {
                            bubbles: true, cancelable: true, view: window,
                            clientX: e.clientX, clientY: e.clientY}));
                    } finally { passing = false; }
                }, true);
            })();
        {% endmacro %}
    """)
    m.add_child(touch)

    HEATMAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(HEATMAP_HTML))
    print(f"Wrote {HEATMAP_HTML}")
    print(f"{len(businesses_in_rings):,} points plotted (within-ring default) / "
          f"{len(businesses):,} available (all-Seattle toggle), across {len(stations)} stations")


if __name__ == "__main__":
    main()
