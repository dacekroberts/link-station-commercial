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
from folium.plugins import HeatMap

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    HEATMAP_HTML,
    RING_EDGES_METERS,
    RING_LABELS,
)

SEATTLE_CENTER = [47.6062, -122.3321]


def main():
    for path in (STATIONS_CSV, BUSINESSES_GEOCODED_CSV):
        if not path.exists():
            sys.exit(f"Missing {path}. Run the earlier steps first.")

    stations = pd.read_csv(STATIONS_CSV)
    businesses = pd.read_csv(BUSINESSES_GEOCODED_CSV)

    m = folium.Map(
        location=SEATTLE_CENTER,
        zoom_start=12,
        tiles="CartoDB positron",  # muted basemap so the heat layer reads clearly
    )

    heat_points = businesses[["latitude", "longitude"]].dropna().values.tolist()
    HeatMap(
        heat_points,
        radius=12,
        blur=18,
        min_opacity=0.3,
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

    folium.LayerControl(collapsed=False).add_to(m)

    HEATMAP_HTML.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(HEATMAP_HTML))
    print(f"Wrote {HEATMAP_HTML}")
    print(f"{len(heat_points):,} points plotted across {len(stations)} stations")


if __name__ == "__main__":
    main()
