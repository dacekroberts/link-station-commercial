"""Step 4: ring buffers, spatial join, and the three analyses.

Input:  data/processed/stations.csv
        data/processed/businesses_geocoded.csv
        data/raw/ridership_by_station.csv
Output: outputs/ring_stats.csv
        outputs/station_stats.csv
        outputs/chain_stats.csv
        outputs/chain_ring_stats.csv

The analytical core, answering three questions:

  1. Ring gradient    - does commercial density fall off with distance?
  2. Ridership        - does station volume relate to commercial density?
  3. Chain footprint  - do multi-location brands cluster near transit?

CRS rule: buffer in CRS_PROJECTED (EPSG:32610, meters), never in
CRS_GEOGRAPHIC (EPSG:4326, degrees). A degree of longitude is about 75 km
at this latitude and a degree of latitude about 111 km, so buffering in
degrees produces ovals of the wrong size. Project, buffer, project back.

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
    CHAIN_RING_STATS_CSV,
    CHAIN_ANALYSIS_EXCLUDE_BRANDS,
)

RIDERSHIP_COL = "avg_monthly_boardings"

# Legal suffixes at the end of a name only, repeated or comma-separated
# ("FOO, INC.", "FOO L.L.C."). Anchored to the end so a word like CO in the
# middle of a name ("PCC CO-OP", "BLUE CO BAKERY") is left alone.
LEGAL_SUFFIXES = re.compile(
    r"(?:[\s,]+(?:LLC|L\.?L\.?C\.?|INC\.?|INCORPORATED|CORP\.?|CORPORATION"
    r"|CO\.?|LTD\.?|LP|LLP|PLLC))+\s*$"
)

# Coordinates rounded to 5 decimals (about 1 m) identify one physical spot.
# Several licenses at one storefront share a spot; see chain_stats below.
SPOT_DECIMALS = 5


def to_gdf(df, lat="latitude", lon="longitude"):
    """Convert a DataFrame with lat/lon columns to a GeoDataFrame in WGS84."""
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


# Known same-chain name variants that exact matching after normalization
# can't merge: a compound-word spacing difference in how the license was
# filed (see docs/DECISIONS.md). An explicit lookup, like GTFS_NAME_ALIASES
# in step1_stations.py, because a general rule would risk merging unrelated
# brands. Keys and values are both already-normalized (post-regex) strings.
BRAND_ALIASES = {
    "RUDYS BARBER SHOP": "RUDYS BARBERSHOP",
}


def normalize_brand(name: str) -> str:
    """Collapse a business name to a comparable brand key.

    Strips legal suffixes, store numbers, and punctuation so that
    "STARBUCKS #1234" and "Starbucks Coffee LLC" resolve together.
    Apostrophes are dropped, not turned into a space, so "Molly Moon's" and
    "Molly Moons" (the same chain, filed inconsistently) share a key.

    Exact matching after normalization catches most chains; known
    compound-word variants are patched via BRAND_ALIASES above. Remaining
    gaps are a disclosed limitation (see the Methodology page). No fuzzy
    matching (e.g. `rapidfuzz`) is used.
    """
    if not isinstance(name, str):
        return ""
    s = name.upper()
    s = s.replace("'", "").replace("’", "")  # ASCII and curly apostrophe
    s = re.sub(r"#\s*\d+", "", s)          # store numbers
    s = LEGAL_SUFFIXES.sub("", " " + s.strip()).strip()
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    s = " ".join(s.split())
    return BRAND_ALIASES.get(s, s)


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
    # appear more than once. Intentional; documented on the Methodology page.
    joined = gpd.sjoin(businesses_proj, rings, how="inner", predicate="within")
    print(f"{len(joined):,} business-ring matches")

    # --- 1. Ring gradient -----------------------------------------------
    # Start from every station-ring and count into it, not from the join:
    # groupby().size() on the join has no row for an empty ring, and a
    # missing row silently drops out of every mean downstream. An empty ring
    # is a real observation (business_count 0), not missing data. Northgate
    # and UW ring 1 and Rainier Beach ring 3 are empty; averaging without
    # them overstated ring 1 by 14% and ring 3 by 7%.
    counts = (
        joined.groupby(["station", "ring"])
        .size()
        .rename("business_count")
    )
    ring_stats = (
        rings[["station", "ring", "ring_index", "area_sq_mi"]]
        .drop_duplicates()
        .merge(counts, on=["station", "ring"], how="left")
        .fillna({"business_count": 0})
        .astype({"business_count": int})
        [["station", "ring", "ring_index", "business_count", "area_sq_mi"]]
    )
    expected = len(stations) * len(RING_LABELS)
    if len(ring_stats) != expected:
        sys.exit(f"ring_stats has {len(ring_stats)} rows, expected {expected} "
                 f"({len(stations)} stations x {len(RING_LABELS)} rings). "
                 "Either build_rings() dropped a ring, or the counts were "
                 "merged without how='left' - an empty ring must stay as a "
                 "row with business_count 0, not disappear.")
    ring_stats["density_per_sq_mi"] = (
        ring_stats["business_count"] / ring_stats["area_sq_mi"]
    )
    ring_stats = ring_stats.sort_values(["station", "ring_index"])

    # Two decimals, not one: a one-decimal print (310.5) invites rounding a
    # second time (to 311) when the true value is 310.48. Round once, from
    # the unrounded mean, as scripts/check_published_numbers.py does.
    print("\nMean density by ring (the gradient):")
    print(
        ring_stats.groupby("ring", sort=False)["density_per_sq_mi"]
        .mean().round(2).to_string()
    )

    # --- 2. Station totals, joined to ridership -------------------------
    # Walkshed density is total businesses over total area within 0.3 mi,
    # not the mean of the three ring densities: ring 1 is a fifth of ring
    # 3's area, and an unweighted mean roughly doubled it at stations with a
    # busy ring 1 (Othello 454 vs a true 230).
    walkshed = ring_stats[ring_stats["ring_index"] <= 2]
    station_stats = (
        walkshed.groupby("station")
        .agg(
            businesses_within_0_3mi=("business_count", "sum"),
            area_sq_mi=("area_sq_mi", "sum"),
        )
        .reset_index()
    )
    station_stats["density_per_sq_mi"] = (
        station_stats["businesses_within_0_3mi"] / station_stats["area_sq_mi"]
    )
    station_stats = station_stats.drop(columns="area_sq_mi")

    if RIDERSHIP_CSV.exists():
        ridership = pd.read_csv(RIDERSHIP_CSV)
        station_stats = station_stats.merge(ridership, on="station", how="left")
        # Named column, not position: a station whose name fails to match
        # gets a blank here, and this warning is the only thing that says so.
        unmatched = station_stats["station"][station_stats[RIDERSHIP_COL].isna()]
        if len(unmatched):
            print(f"\nNo ridership match for: {list(unmatched)}")
            print("Station names must agree between the two files.")
    else:
        print(f"\nNo ridership file at {RIDERSHIP_CSV} - skipping that join.")
        print("See data/raw/README.md for how to export it.")

    # --- 3. Chain footprint ---------------------------------------------
    # A brand at many stations is a firm repeatedly choosing transit
    # adjacency: revealed preference, a stronger signal about location
    # strategy than any raw count.
    name_col = "business_name" if "business_name" in joined.columns else None
    if name_col:
        joined["brand"] = joined[name_col].apply(normalize_brand)
        # Corporate food-service contractors (Compass One, Bon Appetit
        # Management, Flik International) are excluded from the chain
        # analysis only; they still count fully in ring_stats/station_stats
        # above. Each is one vendor's footprint across a single client's
        # office campus, not independent chain site-selection. See
        # CHAIN_ANALYSIS_EXCLUDE_BRANDS in config.py for the reasoning,
        # including why NAICS 722310 alone doesn't cleanly separate these
        # from legitimate small chains.
        excluded = joined["brand"].isin(CHAIN_ANALYSIS_EXCLUDE_BRANDS)
        if excluded.any():
            print(f"{excluded.sum():,} business-ring rows excluded from chain "
                  f"analysis only (contractor brands): "
                  f"{sorted(joined.loc[excluded, 'brand'].unique())}")
        # location_count counts distinct spots, not records. A record is one
        # license, and one storefront can hold several (step 2 can't merge
        # them: each has its own account number). Counting records made 36
        # single-storefront brands look like chains (152 -> 116 brands).
        joined["spot"] = (
            joined["latitude"].round(SPOT_DECIMALS).astype(str) + ","
            + joined["longitude"].round(SPOT_DECIMALS).astype(str)
        )
        chain_stats = (
            joined[(joined["brand"] != "") & ~excluded]
            .groupby("brand")
            .agg(
                station_count=("station", "nunique"),
                location_count=("spot", "nunique"),
            )
            .reset_index()
            # Real chains sort to the top and single-location noise (see
            # below) to the bottom, so no separate filter is needed downstream.
            .sort_values(["location_count", "station_count"], ascending=False)
        )

        # Downtown buffer overlap alone can inflate station_count: one
        # location in the Westlake/Symphony/Pioneer Square/International
        # District overlap can touch up to 4 stations while being one lease
        # decision, not a chain. "Chain" is therefore location_count >= 2,
        # never station_count > 1. Checked by hand: PU POWDER and Saigon
        # Drip Kitchen, one location each, both reached 4 stations.
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

        # --- 3b. Chain share by ring -------------------------------------
        # Does chain presence concentrate near the platform, the question the
        # gradient asks of density? Same counting convention as ring_stats
        # (every business-ring-per-station match counts, downtown-overlap
        # duplicates included), so the two are directly comparable. The
        # denominator is the full joined set, matching ring_stats'
        # population, not just brand-matched rows: blank or unparseable
        # names count as "not a chain", and dropping them from the
        # denominator would inflate the share.
        real_chain_brands = set(true_chains["brand"])
        joined["is_chain"] = joined["brand"].isin(real_chain_brands)
        chain_ring_stats = (
            joined.groupby("ring")
            .agg(
                total_matches=("record_id", "size"),
                chain_matches=("is_chain", "sum"),
            )
            .reindex(RING_LABELS)
        )
        chain_ring_stats["chain_share"] = (
            chain_ring_stats["chain_matches"] / chain_ring_stats["total_matches"]
        )
        chain_ring_stats = chain_ring_stats.reset_index()
        chain_ring_stats.to_csv(CHAIN_RING_STATS_CSV, index=False)
        print("\nChain share by ring:")
        print(chain_ring_stats.to_string(index=False))
    else:
        print("\nNo business_name column - skipping chain analysis.")

    ring_stats.to_csv(RING_STATS_CSV, index=False)
    station_stats.to_csv(STATION_STATS_CSV, index=False)
    print(f"\nWrote outputs to {RING_STATS_CSV.parent}")


if __name__ == "__main__":
    main()
