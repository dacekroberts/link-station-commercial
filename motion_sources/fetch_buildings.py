"""Building footprints for the motion opener's backdrop. Decoration, not data.

Fetches OpenStreetMap building outlines within half a mile of the 1 Line
between Northgate and Rainier Beach, and writes three GeoJSON files to
visuals/data/buildings/ (outside git, never read by the site or pipeline).
Needs the local data/ tree (steps 1 and 2 run) and requirements-pipeline.txt:

  buildings_raw.geojson       every building in the band, full detail
  buildings_line.geojson      the largest footprints, simplified, capped
  buildings_westlake.geojson  every building within 0.6 mi of Westlake

Distances and areas are measured in EPSG:32610; output is EPSG:4326.
Credit wherever these are drawn: (c) OpenStreetMap contributors (ODbL).

Run from the repo root:  python motion_sources/fetch_buildings.py
Pass --offline to rebuild the derived files from the saved Overpass reply.
"""
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, Point, Polygon

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "visuals" / "data" / "buildings"
GTFS_ZIP = REPO / "data" / "raw" / "gtfs.zip"
STATIONS = REPO / "data" / "processed" / "stations.csv"
SHAPE_ID = "N23:S07"  # same shape step5_map.py draws
MILE = 1609.344
BAND_M = 0.5 * MILE
WESTLAKE_M = 0.6 * MILE  # the outer ring's edge
CAP = 8000  # upper end of the 3,000 to 8,000 shapes asked for
SIMPLIFY_M = 1.5
OVERPASS = "https://overpass-api.de/api/interpreter"

OUT.mkdir(parents=True, exist_ok=True)
stations = pd.read_csv(STATIONS)
assert len(stations) == 16, len(stations)

# The rail alignment, trimmed to the stretch between the outermost stations
# (the GTFS shape runs on past the city in both directions).
with zipfile.ZipFile(GTFS_ZIP) as z, z.open("shapes.txt") as f:
    shapes = pd.read_csv(f)
pts = shapes[shapes["shape_id"] == SHAPE_ID].sort_values("shape_pt_sequence")
assert len(pts) > 1, "rail shape not found in this GTFS feed"
lat_hi, lat_lo = stations["latitude"].max(), stations["latitude"].min()
pts = pts[(pts["shape_pt_lat"] <= lat_hi) & (pts["shape_pt_lat"] >= lat_lo)]
line = gpd.GeoSeries(
    [LineString(zip(pts["shape_pt_lon"], pts["shape_pt_lat"]))], crs=4326
).to_crs(32610)
band = line.buffer(BAND_M).iloc[0]

raw_json = OUT / "overpass_reply.json"
if "--offline" not in sys.argv:
    # Overpass takes the polyline as lat,lon pairs; thin it to keep the
    # query short (20 m tolerance is far inside the half-mile band).
    thin = line.simplify(20).to_crs(4326).iloc[0]
    poly = ",".join(f"{y:.5f},{x:.5f}" for x, y in thin.coords)
    query = (
        "[out:json][timeout:300];"
        f'(way["building"](around:{BAND_M:.0f},{poly});'
        f'relation["building"]["type"="multipolygon"](around:{BAND_M:.0f},{poly}););'
        "out geom;"
    )
    print(f"querying Overpass ({len(thin.coords)} line points)...")
    r = requests.post(OVERPASS, data={"data": query}, timeout=600,
                      headers={"User-Agent": "link-station-commercial portfolio visual"})
    r.raise_for_status()
    raw_json.write_bytes(r.content)
    print(f"saved {raw_json.name}: {len(r.content) / 1e6:.1f} MB")

elements = json.loads(raw_json.read_text(encoding="utf-8"))["elements"]


def ring(geom):
    coords = [(p["lon"], p["lat"]) for p in geom]
    return Polygon(coords) if len(coords) >= 4 and coords[0] == coords[-1] else None


polys = []
for el in elements:
    if el["type"] == "way":
        p = ring(el.get("geometry", []))
        if p is not None:
            polys.append(p)
    else:  # multipolygon relation: keep each closed outer ring, ignore holes
        for m in el.get("members", []):
            if m.get("role") == "outer" and m.get("geometry"):
                p = ring(m["geometry"])
                if p is not None:
                    polys.append(p)

g = gpd.GeoDataFrame(geometry=polys, crs=4326).to_crs(32610)
g["geometry"] = g.geometry.buffer(0)  # repair self-touching outlines
g = g[g.is_valid & ~g.is_empty & g.intersects(band)].copy()
g["area_m2"] = g.area.round(1)
g = g.sort_values("area_m2", ascending=False).reset_index(drop=True)


def write(frame, name):
    out = frame.to_crs(4326)
    path = OUT / name
    out.to_file(path, driver="GeoJSON", COORDINATE_PRECISION=6)
    print(f"{name}: {len(out):,} shapes, {path.stat().st_size / 1e6:.2f} MB")


write(g, "buildings_raw.geojson")

top = g.head(CAP).copy()
top["geometry"] = top.geometry.simplify(SIMPLIFY_M)
write(top, "buildings_line.geojson")
print(f"  smallest footprint kept: {top['area_m2'].min():,.0f} m2 "
      f"(of {len(g):,} buildings in the band)")

w = stations[stations["station"] == "Westlake"].iloc[0]
westlake = gpd.GeoSeries([Point(w["longitude"], w["latitude"])], crs=4326).to_crs(32610).iloc[0]
near = g[g.intersects(westlake.buffer(WESTLAKE_M))].copy()
near["geometry"] = near.geometry.simplify(SIMPLIFY_M)
write(near, "buildings_westlake.geojson")

# Share of the capped set by stretch of line, to show how uneven the
# size filter leaves the backdrop.
cy = top.geometry.centroid.to_crs(4326).y
print("  capped set, north of Capitol Hill / downtown stretch / south of Stadium:",
      int((cy > 47.63).sum()), int(((cy <= 47.63) & (cy >= 47.59)).sum()), int((cy < 47.59).sum()))
