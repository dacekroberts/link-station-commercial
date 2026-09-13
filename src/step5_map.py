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
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap, FastMarkerCluster

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    HEATMAP_HTML,
    RING_EDGES_METERS,
    RING_LABELS,
)

SEATTLE_CENTER = [47.6062, -122.3321]

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
# exactly one, so no "Other" bucket is needed. Colors from the Cove
# categorical palette (blue/orange/aqua), chosen for mutual distinguishability
# rather than picked arbitrarily.
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


def main():
    for path in (STATIONS_CSV, BUSINESSES_GEOCODED_CSV):
        if not path.exists():
            sys.exit(f"Missing {path}. Run the earlier steps first.")

    stations = pd.read_csv(STATIONS_CSV)
    businesses = pd.read_csv(BUSINESSES_GEOCODED_CSV, dtype={"naics": str})

    m = folium.Map(
        location=SEATTLE_CENTER,
        zoom_start=12,
        tiles="OpenStreetMap",
        width=1000,
        height=650,
    )

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

    for name, prefixes, color in NAICS_GROUPS:
        rows = businesses[businesses["_group"] == name]
        data = [
            [row.latitude, row.longitude, row.business_name]
            for row in rows.itertuples()
        ]
        if not data:
            continue
        callback = f"""
            function (row) {{
                var marker = L.circleMarker(new L.LatLng(row[0], row[1]), {{
                    radius: 5, color: '{color}', fillColor: '{color}',
                    fillOpacity: 0.85, weight: 1
                }});
                marker.bindPopup(row[2]);
                return marker;
            }}
        """
        # FastMarkerCluster's own `show` param is not reliable for hiding it
        # at load - wrap it in a FeatureGroup instead, the same mechanism the
        # ring layers above use, which does respect show=False.
        # Business COUNT goes in its own parens, separate from the NAICS
        # code (spelled out in naics_label) - the two numbers sitting next
        # to each other in parens was the exact confusion being fixed.
        group = folium.FeatureGroup(
            name=f"Businesses: {naics_label(name, prefixes)} ({len(data):,})",
            show=False,
        )
        FastMarkerCluster(data, callback=callback).add_to(group)
        group.add_to(m)

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
