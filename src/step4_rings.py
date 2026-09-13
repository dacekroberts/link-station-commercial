"""Step 4 - Ring buffers, spatial join, and the three analyses.

Input:  data/processed/stations.csv
        data/processed/businesses_geocoded.csv
        data/raw/ridership_by_station.csv
Output: outputs/ring_stats.csv
        outputs/station_stats.csv
        outputs/chain_stats.csv

This is the analytical core. Three things happen:

  1. Ring gradient    - does commercial density fall off with distance?
  2. Ridership        - does station volume relate to commercial density?
  3. Chain footprint  - do multi-location brands cluster near transit?

THE CRS RULE: buffer in CRS_PROJECTED (metres), never in CRS_GEOGRAPHIC
(degrees). A degree of longitude is about 75 km at this latitude and a
degree of latitude about 111 km, so buffering in degrees produces ovals
of the wrong size. Project, buffer, project back.

Run:  python src/step4_rings.py
"""

import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    CRS_GEOGRAPHIC,
    CRS_PROJECTED,
    RING_EDGES_METERS,
    RING_LABELS,
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    RIDERSHIP_CSV,
    RING_STATS_CSV,
    STATION_STATS_CSV,
    CHAIN_STATS_CSV,
)

LEGAL_SUFFIXES = r"\b(LLC|L\.L\.C\.|INC|INCORPORATED|CORP|CORPORATION|CO|LTD|LP|LLP|PLLC)\b"


def to_gdf(df, lat="latitude", lon="longitude"):
    """DataFrame with lat/lon columns -> GeoDataFrame in WGS84."""
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df[lon], df[lat]),
        crs=CRS_GEOGRAPHIC,
    )


def build_rings(stations_gdf):
    """Annular ring polygons around each station, in the projected CRS.

    Rings are annuli, not nested circles: ring 2 is the 0.1-0.2 mile band
    with the inner disc removed. Without the subtraction every business
    would count in every outer ring and the gradient would be meaningless.
    """
    projected = stations_gdf.to_crs(CRS_PROJECTED)
    rows = []

    for _, station in projected.iterrows():
        for i, label in enumerate(RING_LABELS):
            inner_m, outer_m = RING_EDGES_METERS[i], RING_EDGES_METERS[i + 1]
            outer = station.geometry.buffer(outer_m)
            ring = outer.difference(station.geometry.buffer(inner_m)) if inner_m > 0 else outer
            rows.append({
                "station": station["station"],
                "ring": label,
                "ring_index": i,
                "area_sq_mi": ring.area / (1609.344 ** 2),
                "geometry": ring,
            })

    return gpd.GeoDataFrame(rows, crs=CRS_PROJECTED)


def normalize_brand(name: str) -> str:
    """Collapse a business name to a comparable brand key.

    Strips legal suffixes, store numbers, and punctuation so that
    "STARBUCKS #1234" and "Starbucks Coffee LLC" resolve together.

    Exact matching after normalization catches most chains. If you have
    time, `rapidfuzz` will catch the rest - but check its matches by hand
    before trusting them.
    """
    if not isinstance(name, str):
        return ""
    s = name.upper()
    s = re.sub(r"#\s*\d+", "", s)          # store numbers
    s = re.sub(LEGAL_SUFFIXES, "", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return " ".join(s.split())


def main():
    for path in (STATIONS_CSV, BUSINESSES_GEOCODED_CSV):
        if not path.exists():
            sys.exit(f"Missing {path}. Run the earlier steps first.")

    stations = to_gdf(pd.read_csv(STATIONS_CSV))
    businesses = to_gdf(pd.read_csv(BUSINESSES_GEOCODED_CSV, dtype=str).astype(
        {"latitude": float, "longitude": float}
    ))
    print(f"{len(stations)} stations, {len(businesses):,} businesses")

    rings = build_rings(stations)
    businesses_proj = businesses.to_crs(CRS_PROJECTED)

    # Businesses in overlapping downtown rings match multiple stations and
    # appear more than once. That is intentional and documented - see the
    # methodology page.
    joined = gpd.sjoin(businesses_proj, rings, how="inner", predicate="within")
    print(f"{len(joined):,} business-ring matches")

    # --- 1. Ring gradient -----------------------------------------------
    ring_stats = (
        joined.groupby(["station", "ring", "ring_index"])
        .size()
        .reset_index(name="business_count")
        .merge(
            rings[["station", "ring", "area_sq_mi"]].drop_duplicates(),
            on=["station", "ring"],
        )
    )
    ring_stats["density_per_sq_mi"] = (
        ring_stats["business_count"] / ring_stats["area_sq_mi"]
    )
    ring_stats = ring_stats.sort_values(["station", "ring_index"])

    print("\nMean density by ring (the gradient):")
    print(
        ring_stats.groupby("ring", sort=False)["density_per_sq_mi"]
        .mean().round(1).to_string()
    )

    # --- 2. Station totals, joined to ridership -------------------------
    walkshed = ring_stats[ring_stats["ring_index"] <= 2]
    station_stats = (
        walkshed.groupby("station")
        .agg(
            businesses_within_0_3mi=("business_count", "sum"),
            density_per_sq_mi=("density_per_sq_mi", "mean"),
        )
        .reset_index()
    )

    if RIDERSHIP_CSV.exists():
        ridership = pd.read_csv(RIDERSHIP_CSV)
        station_stats = station_stats.merge(ridership, on="station", how="left")
        unmatched = station_stats["station"][station_stats.iloc[:, -1].isna()]
        if len(unmatched):
            print(f"\nNo ridership match for: {list(unmatched)}")
            print("Station names must agree between the two files.")
    else:
        print(f"\nNo ridership file at {RIDERSHIP_CSV} - skipping that join.")
        print("See data/raw/README.md for how to export it.")

    # --- 3. Chain footprint ---------------------------------------------
    # A brand appearing at many stations is a firm systematically choosing
    # transit adjacency. That is revealed preference, and a stronger signal
    # about location strategy than any raw count.
    name_col = "business_name" if "business_name" in joined.columns else None
    if name_col:
        joined["brand"] = joined[name_col].apply(normalize_brand)
        chain_stats = (
            joined[joined["brand"] != ""]
            .groupby("brand")
            .agg(
                station_count=("station", "nunique"),
                location_count=("record_id", "nunique"),
            )
            .reset_index()
            # Real chains float to the top; single-location noise (see below)
            # sorts to the bottom without needing a separate filter downstream.
            .sort_values(["location_count", "station_count"], ascending=False)
        )

        # A brand's station_count can be inflated by the downtown overlap
        # alone: one physical location inside the Westlake/Symphony/Pioneer
        # Square/International District overlap zone can touch up to 4
        # stations without being a chain at all - it made one lease
        # decision, not four. "Chain" is therefore defined as
        # location_count >= 2, never station_count > 1. Verified by hand
        # (Session 6): PU POWDER and Saigon Drip Kitchen, each one real
        # location, both showed up at 4 stations before this was caught.
        overlap_noise = (
            (chain_stats["location_count"] == 1) & (chain_stats["station_count"] > 1)
        ).sum()
        print(f"\n{overlap_noise:,} of {len(chain_stats):,} normalized brands touch "
              ">1 station from a single physical location (downtown buffer "
              "overlap, not a chain) - excluded from the chain count below.")

        true_chains = chain_stats[chain_stats["location_count"] > 1]
        print(f"{len(true_chains):,} brands have 2+ real locations. "
              "Present at the most stations:")
        print(
            true_chains.sort_values("station_count", ascending=False)
            .head(15).to_string(index=False)
        )
        chain_stats.to_csv(CHAIN_STATS_CSV, index=False)
    else:
        print("\nNo business_name column - skipping chain analysis.")

    ring_stats.to_csv(RING_STATS_CSV, index=False)
    station_stats.to_csv(STATION_STATS_CSV, index=False)
    print(f"\nWrote outputs to {RING_STATS_CSV.parent}")


if __name__ == "__main__":
    main()
