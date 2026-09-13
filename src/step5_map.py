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

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    HEATMAP_HTML,
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
<div style="
    position: fixed; bottom: 24px; left: 24px; z-index: 9999;
    background: white; padding: 10px 14px; border: 1px solid #999;
    border-radius: 4px; font-family: sans-serif; font-size: 13px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.3);
">
  <div style="font-weight: bold; margin-bottom: 6px;">Business category</div>
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

    m = folium.Map(
        location=SEATTLE_CENTER,
        zoom_start=12,
        tiles=None,  # added explicitly below, so its layer-control name is ours to set
        width=1000,
        height=650,
    )
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Seattle 1 Line Business Density Heatmap",
    ).add_to(m)

    heat_points = businesses[["latitude", "longitude"]].dropna().values.tolist()
    HeatMap(
        heat_points,
        radius=HEAT_RADIUS,
        blur=HEAT_BLUR,
        min_opacity=HEAT_MIN_OPACITY,
        name="Commercial density",
    ).add_to(m)

    # Ring circles, each toggleable so the map is not overwhelming at load.
    for i, label in enumerate(RING_LABELS):
        layer = folium.FeatureGroup(name=f"Ring: {label}", show=(i == 2))
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

    station_layer = folium.FeatureGroup(name="Stations")
    for _, station in stations.iterrows():
        folium.CircleMarker(
            location=[station["latitude"], station["longitude"]],
            radius=5,
            color="#1a5490",
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(station["station"], max_width=200),
        ).add_to(station_layer)
    station_layer.add_to(m)

    # --- The rail line itself - important visual context, on by default ---
    rail_coords = load_rail_line_shape()
    if rail_coords:
        rail_layer = folium.FeatureGroup(name="Link 1 Line route", show=True)
        folium.PolyLine(
            rail_coords, color="#0a7a3c", weight=5, opacity=0.85,
        ).add_to(rail_layer)
        # A large, high-contrast label - not a hover tooltip, always visible.
        # Anchored at Othello, well south of downtown: checked visually, not
        # assumed - a computed centroid of all 16 stations, and even Beacon
        # Hill, both still landed under the (now quite tall) layer control
        # panel at the default zoom, since the downtown station cluster
        # pulls any average north and the panel has grown with each new
        # layer added this session.
        label_station = stations.loc[stations["station"] == "Othello"].iloc[0]
        label_lat, label_lon = label_station["latitude"], label_station["longitude"]
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
    # 11,409 points is too many for plain (unclustered) markers - overlapping
    # dots at any zoom level a viewer would actually use, and a much heavier
    # file. FastMarkerCluster ships a compact coordinate array and clusters
    # client-side, rather than one full Marker object per point. Off by
    # default (show=False): this is a detail layer, not what a first-time
    # viewer should load into.
    businesses = businesses.dropna(subset=["latitude", "longitude"])
    businesses["_group"], businesses["_color"] = zip(
        *businesses["naics"].map(naics_group)
    )
    unmatched = businesses["_group"].isna().sum()
    if unmatched:
        print(f"WARNING: {unmatched} businesses matched no NAICS group - "
              "check NAICS_GROUPS against NAICS_STOREFRONT_PREFIXES in config.py")

    # Nearest station + ring band, for the hover tooltip only - see
    # nearest_station_and_ring()'s docstring for why this is a separate,
    # simpler computation from step4's overlap-aware ring_stats.
    businesses["nearest_station"], businesses["ring_band"] = nearest_station_and_ring(
        businesses, stations
    )

    def add_pin_layer(rows, sublabel, group_name, color):
        """One toggleable, clustered, coloured pin layer - the one pattern
        reused for every business layer below, broad or fine-grained."""
        data = [
            [row.latitude, row.longitude, row.business_name, row.naics,
             row.nearest_station, row.ring_band]
            for row in rows.itertuples()
        ]
        if not data:
            return
        callback = f"""
            function (row) {{
                var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {{
                    radius: 5, color: '{color}', fillColor: '{color}',
                    fillOpacity: 0.85, weight: 1
                }});
                var html = '<b>' + row[2] + '</b><br>' +
                    'NAICS code: ' + row[3] + '<br>' +
                    'Nearest station: ' + row[4] + '<br>' +
                    row[5];
                marker.bindTooltip(html, {{sticky: true}});
                return marker;
            }}
        """
        # FastMarkerCluster's own `show` param is not reliable for hiding it
        # at load - wrap it in a FeatureGroup instead, the same mechanism the
        # ring layers above use, which does respect show=False.
        # Business COUNT goes in its own parens, separate from any NAICS
        # code mentioned in the label - two numbers sitting next to each
        # other in parens was the exact confusion fixed earlier.
        layer_name = f"Businesses: {group_name} — {sublabel} ({len(data):,})"
        fg = folium.FeatureGroup(name=layer_name, show=False)
        FastMarkerCluster(data, callback=callback).add_to(fg)
        fg.add_to(m)

    for name, prefixes, color in NAICS_GROUPS:
        group_rows = businesses[businesses["_group"] == name]

        # The broad group as a whole, toggleable on its own - unchanged
        # from before.
        add_pin_layer(group_rows, naics_label(name, prefixes), name, color)

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

    folium.LayerControl(collapsed=False).add_to(m)

    HEATMAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(HEATMAP_HTML))
    print(f"Wrote {HEATMAP_HTML}")
    print(f"{len(heat_points):,} points plotted across {len(stations)} stations")


if __name__ == "__main__":
    main()
