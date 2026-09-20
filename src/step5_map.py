"""Step 5 - Render the heatmap to a standalone HTML file.

Input:  data/processed/stations.csv
        data/processed/businesses_geocoded.csv
Output: outputs/heatmap.html

The saved file is self-contained: openable in any browser, embeddable in
Streamlit, droppable in a portfolio. It is the project's visual anchor.

A note on what the heatmap shows. Leaflet's heat layer applies a visual
blur, not a statistical density estimate - the radius is a rendering choice,
not a bandwidth. Treat it as illustration. The ring statistics from step 4
are what carry your quantitative claims.

Run:  python src/step5_map.py
"""

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
# route_id 100479 is the real 1 Line (exact match on route_short_name - see
# step1_stations.py for why substring matching pulled in the shuttle
# bus-bridge route instead). N23:S07 is that route's most-used shape
# (2,815 of 5,404 trips, Session 7 check) - one full-line direction, not a
# short-turn variant. The two directions are near-mirror images, so either
# would do; this one was simply more common.
RAIL_LINE_SHAPE_ID = "N23:S07"

# Heat layer tuning (Session 7). Leaflet.heat pixel-space params, not a
# statistical bandwidth - chosen by eye across a few candidates for legibility
# at the default city-wide zoom, where radius=12/blur=18 read as one
# undifferentiated wash. Tighter values keep individual neighbourhood
# clusters distinguishable there, at no real cost once zoomed into downtown.
HEAT_RADIUS = 8
HEAT_BLUR = 10
HEAT_MIN_OPACITY = 0.35

# Leaflet.heat's own default gradient runs blue -> cyan -> lime -> yellow ->
# red - most of the visible area at typical densities reads as blue/cyan,
# which several readers found counterintuitive for a "heat" map (blue reads
# as cold, not low-but-nonzero). Replaced with a single-hue ramp - pale at
# low density through deep at peak - so it reads as one color getting
# stronger, not a color-name change partway up the scale. Originally
# ColorBrewer Reds; now an orange ramp based on Schematic 1 and the Findings
# page ring bars, shifted one step more saturated at the low end (the
# palest peach was nearly invisible on the light OSM tiles, since
# Leaflet.heat opacity follows density) plus a deeper #8F3A05 peak.
HEAT_GRADIENT = {0.3: "#FBB878", 0.5: "#F97316", 0.7: "#DE6412", 0.85: "#C0570F", 1.0: "#8F3A05"}

# Same three groups NAICS_STOREFRONT_PREFIXES already defines in config.py
# (retail, food service, personal services) - every kept business falls into
# exactly one, so no top-level "Other" bucket is needed. Colors from the
# Cove categorical palette (blue/orange/aqua), chosen for mutual
# distinguishability rather than picked arbitrarily.
#
# name / prefixes / color. Labels spell out "NAICS Code:" rather than just
# putting the digits in parens - "Retail (44/45)" sat right next to a
# business COUNT in parens too (e.g. "(5,221)") in the layer control,
# and the two different kinds of number were easy to mistake for each other.
NAICS_GROUPS = [
    ("Retail", ("44", "45"), "#2a78d6"),
    ("Food service", ("722",), "#eb6834"),
    ("Personal services", ("812",), "#1baf7a"),
]

# Finer, toggleable splits within each broad group (Session 7 add-on) - the
# top few specific NAICS codes by count, plus an "Other" residual for
# everything else in that group. Same color as the parent group throughout:
# these layers refine WHICH businesses of a colour show, they don't add new
# colours, so the legend (3 rows, unchanged) still tells the whole story.
# Real category names and codes pulled from the actual data, not guessed.
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
    """Real 1 Line route geometry from GTFS shapes.txt - the actual rail
    alignment (curves and all), not a straight line drawn between stations.
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
    """For each business: its nearest station (straight-line) and which ring
    band that distance falls in relative to THAT station specifically.

    Deliberately separate from step4_rings.py's ring_stats: that analysis
    assigns a business to every station whose buffer contains it (including
    downtown overlap, on purpose - see DECISIONS.md). This is a single
    nearest-station view, built only for the pin tooltip, not a
    re-derivation of the ring analysis or a replacement for it.
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

    # `businesses` (all 11,409, citywide) stays the full set throughout -
    # kept around so the "all Seattle businesses" heat toggle below has
    # something to draw from. `businesses_in_rings` is the subset that
    # actually falls within some station's outer ring (0.6 mi), and is
    # what the map opens on by default and what every pin layer uses.
    # Nearest-station distance is used rather than a fresh
    # union-of-buffers computation: if a business's CLOSEST station is
    # already farther than the outer ring edge, every other station is
    # farther still, so "nearest station within 0.6 mi" and "inside at
    # least one station's buffer" are the same condition. Defaulting to
    # the ring-only view matters because step4_rings.py's actual
    # gradient/chain analysis only ever counts ring-bounded businesses -
    # a map that opened on the unbounded citywide picture would be the
    # odd one out and overstate how spread out the analysis's universe is.
    businesses["nearest_station"], businesses["ring_band"] = nearest_station_and_ring(
        businesses, stations
    )
    businesses_in_rings = businesses[
        ~businesses["ring_band"].str.startswith("Beyond")
    ].copy()
    print(f"{len(businesses) - len(businesses_in_rings):,} of {len(businesses):,} "
          f"businesses fall outside every station's ring "
          f"({len(businesses_in_rings):,} remain within a ring).")

    # Persisted for the intro page's "citywide coverage" metric - this count
    # was previously console-only (see above). Deliberately the deduplicated
    # nearest-station figure, not step4_rings.py's business-ring MATCH count
    # (6,847, which double-counts a business once per overlapping station's
    # buffer): a business is either within walking distance of the network
    # or it isn't, so a citywide "how much of Seattle's commercial footprint
    # is within reach of a station" stat should count it once.
    pd.DataFrame([{
        "businesses_in_rings": len(businesses_in_rings),
        "businesses_citywide": len(businesses),
    }]).to_csv(CITYWIDE_COVERAGE_CSV, index=False)

    m = folium.Map(
        location=SEATTLE_CENTER,
        zoom_start=12,
        tiles=None,  # added explicitly below, so its layer-control name is ours to set
        width=1000,
        height=650,
    )
    light_tiles = folium.TileLayer(
        tiles="OpenStreetMap",
        name="Light Mode",
        control=False,
    ).add_to(m)
    # Dark option: the same OSM tiles (no new provider, no API key - see
    # DECISIONS.md on why CartoDB was ruled out) recoloured in the browser by
    # a CSS filter on this layer's own tile container (class defined below).
    # Both base layers are kept out of the layer control (control=False): a
    # separate button, added near the end of main(), swaps between them, so
    # the layer control lists only overlays. Overlays (rings, heat, pins) sit
    # in other panes and are untouched by the filter.
    dark_tiles = folium.TileLayer(
        tiles="OpenStreetMap",
        name="Dark Mode",
        class_name="dark-osm-tiles",
        show=False,
        control=False,
    ).add_to(m)

    # Two heat layers, same tuning, different universe. Within-rings is the
    # default (matches what the rest of the project actually analyzes - see
    # DECISIONS.md); all-Seattle is an explicit opt-in for citywide context,
    # off by default so the map opens on the same scope as the Findings
    # page rather than the broader, less-meaningful citywide picture.
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

    # Ridership (Session 5: 2025 average of monthly totals - see
    # DECISIONS.md for why that metric, not "average weekday boardings").
    # Left join, not inner: a station missing from the CSV should still get
    # a marker, just with no ridership figure, rather than vanish silently.
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

    # control=False - always on, not a togglable layer control entry. Same
    # treatment as the rail line below: both are baseline map context, not
    # an optional data layer the reader would want to hide.
    station_layer = folium.FeatureGroup(name="Stations", control=False)
    for _, station in stations.iterrows():
        boardings = station["avg_monthly_boardings"]
        # Label first, value second - matches the business tooltip's
        # "NAICS code: 722513" convention, not "722513 NAICS code". Spells
        # out "average of monthly totals" rather than just "avg. monthly
        # boardings" - this project deliberately is NOT average WEEKDAY or
        # average DAILY boardings (see DECISIONS.md, Session 5), and a
        # label ambiguous between those and this metric is exactly the kind
        # of mislabeling this project has been careful to avoid elsewhere.
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

    # --- The rail line itself - important visual context, on by default ---
    rail_coords = load_rail_line_shape()
    if rail_coords:
        rail_layer = folium.FeatureGroup(name="Link 1 Line route", show=True, control=False)
        folium.PolyLine(
            rail_coords, color="#0a7a3c", weight=5, opacity=0.85,
        ).add_to(rail_layer)
        # A large, high-contrast label - not a hover tooltip, always visible.
        # Anchored at Westlake's latitude (the heart of the downtown
        # corridor) but offset well west of it, out over Elliott Bay/
        # Myrtle Edwards Park - clear of the dense heat/pin corridor itself
        # and, checked visually, clear of the layer control too. (Earlier
        # attempts - a computed station centroid, then Beacon Hill, then
        # Othello - moved south instead of west and kept landing under the
        # panel or off in the least interesting part of the map.)
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

    # --- Individual business pins, one clustered layer per NAICS group ----
    # Even after the ring filter above, plain (unclustered) markers would
    # overlap and be unreadable at any zoom a viewer would actually use, and
    # a much heavier file. FastMarkerCluster ships a compact coordinate array
    # and clusters client-side, rather than one full Marker object per
    # point. The three broad NAICS-group layers are on by default; the finer
    # subcategory splits stay off - still a detail layer, not what a
    # first-time viewer should load into.
    #
    # Pins stay ring-only even though the heat layer now offers an
    # all-Seattle toggle - doubling all 15 pin layers to cover the citywide
    # set too would double an already-large layer-control menu for a detail
    # view few viewers will open, for businesses outside this project's
    # actual analysis scope. The heat toggle above covers the "what does
    # citywide context look like" need on its own.
    #
    # nearest_station / ring_band (used below for the hover tooltip) were
    # already computed above, on the full pre-filter set, to do the ring
    # filtering itself - see nearest_station_and_ring()'s docstring for why
    # this is a separate, simpler computation from step4's overlap-aware
    # ring_stats.
    businesses_in_rings["_group"], businesses_in_rings["_color"] = zip(
        *businesses_in_rings["naics"].map(naics_group)
    )
    unmatched = businesses_in_rings["_group"].isna().sum()
    if unmatched:
        print(f"WARNING: {unmatched} businesses matched no NAICS group - "
              "check NAICS_GROUPS against NAICS_STOREFRONT_PREFIXES in config.py")

    def add_pin_layer(rows, sublabel, group_name, color, bold=False, show=False):
        """One toggleable, clustered, coloured pin layer - the one pattern
        reused for every business layer below, broad or fine-grained.

        bold=True marks a macro (whole-NAICS-group) layer in the layer
        control, distinguishing it from the finer subcategory splits below
        it - Leaflet renders a layer control's name as HTML, so a literal
        <b> tag in the string is enough, no extra styling needed. The three
        bold macro layers are also the only pin layers on by default
        (show=True) - the finer subcategory splits stay off, still a detail
        view few viewers will open."""
        data = [
            [row.latitude, row.longitude, row.business_name, row.naics,
             row.nearest_station, row.ring_band]
            for row in rows.itertuples()
        ]
        if not data:
            return
        callback = f"""
            function (row) {{
                // business_name comes straight from the City's license
                // registry as free text - a name containing '&' or '<'
                // (e.g. "Smith & Sons") would otherwise break this
                // tooltip's HTML or inject markup. The other fields
                // below are computed/controlled values, not at risk.
                function esc(s) {{
                    return String(s).replace(/&/g, '&amp;')
                        .replace(/</g, '&lt;').replace(/>/g, '&gt;');
                }}
                var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {{
                    radius: 5, color: '{color}', fillColor: '{color}',
                    fillOpacity: 0.85, weight: 1
                }});
                var html = '<b>' + esc(row[2]) + '</b><br>' +
                    'NAICS code: ' + row[3] + '<br>' +
                    'Nearest station: ' + row[4] + '<br>' +
                    row[5];
                marker.bindTooltip(html, {{sticky: true}});
                return marker;
            }}
        """
        # Leaflet.markercluster's default iconCreateFunction hands every
        # cluster the same fixed 40x40px icon regardless of how many points
        # it holds - a 2-point cluster gets exactly as large a hit area as a
        # 500-point one. At the boundary where a cluster is about to split
        # into individual markers, that oversized hit area sits on top of
        # (and blocks hovering) whichever lone dot happens to render right
        # next to it - caught via screenshot on the Heatmap page. Scaling
        # icon size (and therefore hit area) down for small clusters fixes
        # this at the source rather than just tuning cluster radius/zoom
        # thresholds, which would only make the collision less likely, not
        # eliminate it.
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
        # FastMarkerCluster's own `show` param is not reliable for hiding it
        # at load - wrap it in a FeatureGroup instead, the same mechanism the
        # ring layers above use, which does respect show=False.
        # Business COUNT goes in its own parens, separate from any NAICS
        # code mentioned in the label - two numbers sitting next to each
        # other in parens was the exact confusion fixed earlier.
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
        # just the code, not naics_label(name, prefixes) - add_pin_layer
        # already prefixes group_name, so passing the full "{name} — NAICS
        # Code: ..." label here doubled the name
        # ("Retail — Retail — NAICS Code: 44/45"), caught by the user.
        add_pin_layer(
            group_rows, f"NAICS Code: {'/'.join(prefixes)}", name, color, bold=True, show=True
        )

    for name, prefixes, color in NAICS_GROUPS:
        group_rows = businesses_in_rings[businesses_in_rings["_group"] == name]

        # Finer splits within it (Session 7 add-on, cheap reuse of the same
        # pattern): a few specific NAICS codes by count, plus "Other" for
        # the rest of the group. Same colour throughout - see
        # NAICS_SUBCATEGORIES comment above for why.
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

    # Collapsed by default: with 23 toggleable layers now (4 rings + 15
    # business layers + heat/stations/rail), an always-open panel covered a
    # large share of the map. Collapsed, it's a small icon until clicked - a
    # true nested/collapsible-group control (e.g. one "Businesses" dropdown
    # holding all 15) would need a custom Leaflet control or a third-party
    # plugin, real new complexity for a polish feature; this uses only
    # Leaflet's own built-in collapsed state plus a height cap, so the panel
    # never covers the whole map even fully expanded.
    #
    # position="topleft", not Leaflet's topright default: the map has a
    # fixed 1000px width (needed for the Leaflet.heat init-race fix above),
    # and Streamlit's content area is often narrower than that once the
    # sidebar is open - a topright control gets pushed past the visible/
    # scrollable edge and effectively disappears. topleft sits right under
    # the zoom control, which Leaflet stacks automatically, and is visible
    # at any width since it's anchored to the map's origin corner.
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
               the colour swap (water stays blue-ish, not orange), and the
               brightness/saturate tweaks keep it from glaring. */
            .dark-osm-tiles {
                filter: invert(1) hue-rotate(180deg) brightness(0.85)
                        contrast(0.9) saturate(0.7);
            }
            /* Everything below applies only while Dark Mode is selected (the
               class sits on <body> so the legend, which lives outside the
               Leaflet container, is covered too). Colours match the site's
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
    # topleft controls in the order they are added, and this is added after
    # LayerControl). Top-left rather than top-right for the same reason as the
    # layer control: the map is a fixed 1000px wide, so a top-right button can
    # sit past the visible edge. It swaps the two base layers directly and
    # puts a `dark-base` class on <body> so the CSS above can restyle the
    # overlays and controls (body, not the map container, so the legend -
    # which lives outside the container - is covered too). No state is kept
    # beyond that class. A MacroElement rather than a bare script Element: it
    # renders after the map variable exists (a bare one lands above it and
    # throws).
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
                        function render(isDark) {
                            btn.setAttribute('data-mode', isDark ? 'dark' : 'light');
                            btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
                            btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
                        }
                        render(false);
                        function toggle() {
                            var toDark = !map.hasLayer(dark);
                            if (toDark) {
                                map.addLayer(dark);
                                map.removeLayer(light);
                            } else {
                                map.addLayer(light);
                                map.removeLayer(dark);
                            }
                            document.body.classList.toggle('dark-base', toDark);
                            render(toDark);
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

    HEATMAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(HEATMAP_HTML))
    print(f"Wrote {HEATMAP_HTML}")
    print(f"{len(businesses_in_rings):,} points plotted (within-ring default) / "
          f"{len(businesses):,} available (all-Seattle toggle), across {len(stations)} stations")


if __name__ == "__main__":
    main()
