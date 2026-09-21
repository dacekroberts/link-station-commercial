"""Step 3 - Geocode addresses: GIS donor join, then Census for the rest.

Input:  data/processed/businesses_clean.csv
        data/raw/business_licenses_geocoded.geojson  (GIS geometry donor)
Output: data/processed/businesses_geocoded.csv

Two sources, in order:

1. GIS donor join. `business_licenses_geocoded.geojson` is the same
   businesses, pre-geocoded by the City (EPSG:2926, WA State Plane feet).
   Left-join its coordinates onto the clean set by City Account Number -
   authoritative City geocoding, no API call, covers ~90% of rows.
2. Census bulk geocoder, for whatever the donor join didn't match. Free, no
   API key, CSV in and CSV out, 10,000 rows per request, so this batches.
   Required input format is positional and headerless:

       unique_id, street, city, state, zip

   Batches are cached to data/raw/geocode_cache/. Re-running skips completed
   batches, so a timeout partway through costs you one batch, not the run.

The donor layer is NOT the canonical business-license source - see
CLAUDE.md and docs/DECISIONS.md. It contributes geometry only, for rows the clean
CSV already decided to keep.

Run:  python src/step3_geocode.py
"""

import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    BUSINESSES_CLEAN_CSV,
    BUSINESSES_GEOCODED_CSV,
    KING_COUNTY_BBOX,
    CRS_GEOGRAPHIC,
)

DONOR_GEOJSON = DATA_RAW / "business_licenses_geocoded.geojson"
DONOR_CRS = "EPSG:2926"  # WA State Plane North, feet - not declared in the file itself

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE = 5000       # under the 10k ceiling; smaller batches fail less often
CACHE_DIR = DATA_RAW / "geocode_cache"

RESULT_COLUMNS = [
    "record_id", "input_address", "match_status", "match_type",
    "matched_address", "coordinates", "tiger_line_id", "side",
]


def load_donor_lookup() -> pd.DataFrame:
    """account_number -> latitude, longitude from the GIS geometry donor.

    Reprojects EPSG:2926 (feet) to CRS_GEOGRAPHIC directly - a real
    coordinate transform, not the degree-buffering mistake the CRS
    invariant warns about. A handful of account numbers repeat with
    identical coordinates in the source file; kept first, dropped rest.
    """
    if not DONOR_GEOJSON.exists():
        print(f"No GIS donor file at {DONOR_GEOJSON} - skipping, Census will "
              "geocode everything. See data/raw/README.md.")
        return pd.DataFrame(columns=["account_number", "latitude", "longitude"])

    gdf = gpd.read_file(DONOR_GEOJSON)
    gdf = gdf.set_crs(DONOR_CRS, allow_override=True).to_crs(CRS_GEOGRAPHIC)

    before = len(gdf)
    gdf = gdf.drop_duplicates(subset="BUSLIC_CITYACCTNUM")
    if before != len(gdf):
        print(f"Donor file: dropped {before - len(gdf):,} duplicate account numbers")

    donor = pd.DataFrame({
        "account_number": gdf["BUSLIC_CITYACCTNUM"].astype(str),
        "latitude": gdf.geometry.y,
        "longitude": gdf.geometry.x,
    })
    return donor


def geocode_batch(batch: pd.DataFrame, batch_num: int) -> pd.DataFrame:
    """Send one batch to the Census geocoder, caching the response."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"batch_{batch_num:03d}.csv"

    if cache_file.exists():
        print(f"  batch {batch_num}: cached")
        return pd.read_csv(cache_file, header=None, names=RESULT_COLUMNS, dtype=str)

    payload = batch[["record_id", "street_clean", "city", "state", "zip"]]
    csv_bytes = payload.to_csv(index=False, header=False).encode("utf-8")

    response = requests.post(
        GEOCODER_URL,
        files={"addressFile": ("batch.csv", csv_bytes, "text/csv")},
        data={"benchmark": "Public_AR_Current"},
        timeout=600,
    )
    response.raise_for_status()

    cache_file.write_bytes(response.content)
    print(f"  batch {batch_num}: {len(batch)} rows geocoded")

    return pd.read_csv(cache_file, header=None, names=RESULT_COLUMNS, dtype=str)


def in_king_county(df: pd.DataFrame) -> pd.DataFrame:
    """Sanity bounds. Catches swapped lat/lon and wild mismatches."""
    b = KING_COUNTY_BBOX
    before = len(df)
    df = df[
        df["latitude"].between(b["lat_min"], b["lat_max"])
        & df["longitude"].between(b["lon_min"], b["lon_max"])
    ]
    if before != len(df):
        print(f"  dropped {before - len(df):,} points outside King County bounds")
    return df


def main():
    if not BUSINESSES_CLEAN_CSV.exists():
        sys.exit(f"Run step2_clean_businesses.py first - no {BUSINESSES_CLEAN_CSV}")

    df = pd.read_csv(BUSINESSES_CLEAN_CSV, dtype=str)
    print(f"{len(df):,} addresses to geocode\n")

    # --- 1. GIS donor join -----------------------------------------------
    donor = load_donor_lookup()
    df = df.merge(donor, on="account_number", how="left")
    df["geocode_source"] = df["latitude"].notna().map({True: "donor", False: None})

    donor_matched = df[df["geocode_source"] == "donor"].copy()
    donor_matched = in_king_county(donor_matched)
    df.loc[~df["record_id"].isin(donor_matched["record_id"]), "geocode_source"] = None

    donor_rate = len(donor_matched) / len(df) if len(df) else 0
    print(f"Donor join: {len(donor_matched):,} of {len(df):,} matched ({donor_rate:.1%})")

    # --- 2. Census geocoder for the remainder -----------------------------
    remainder = df[df["geocode_source"].isna()].drop(columns=["latitude", "longitude"])
    print(f"\nSending {len(remainder):,} unmatched rows to the Census geocoder "
          f"in batches of {BATCH_SIZE}\n")

    results = []
    for i in range(0, len(remainder), BATCH_SIZE):
        batch = remainder.iloc[i:i + BATCH_SIZE]
        results.append(geocode_batch(batch, i // BATCH_SIZE))
        time.sleep(1)

    census_matched = pd.DataFrame(columns=["record_id", "latitude", "longitude", "match_type"])
    if results:
        geo = pd.concat(results, ignore_index=True)

        # The geocoder returns "lon,lat" in one field. Note the order.
        census_matched = geo[geo["match_status"] == "Match"].copy()
        coords = census_matched["coordinates"].str.split(",", expand=True)
        census_matched["longitude"] = pd.to_numeric(coords[0], errors="coerce")
        census_matched["latitude"] = pd.to_numeric(coords[1], errors="coerce")
        census_matched = in_king_county(census_matched)

    census_rate = len(census_matched) / len(remainder) if len(remainder) else 0
    print(f"\nCensus match rate on the remainder: {census_rate:.1%} "
          f"({len(census_matched):,} of {len(remainder):,})")
    if census_rate < 0.80 and len(remainder) > 0:
        print(
            "Below 80%. Usually address formatting. Try the `usaddress` "
            "library in step 2 to parse street strings into components."
        )

    # --- Combine both sources ---------------------------------------------
    census_matched = census_matched[["record_id", "latitude", "longitude"]].copy()
    census_matched["geocode_source"] = "census"

    donor_out = donor_matched[["record_id", "latitude", "longitude", "geocode_source"]]
    combined_geo = pd.concat([donor_out, census_matched], ignore_index=True)

    base = df.drop(columns=["latitude", "longitude", "geocode_source"])
    out = base.merge(combined_geo, on="record_id", how="inner")

    overall_rate = len(out) / len(df) if len(df) else 0
    print(f"\nOverall: {len(out):,} of {len(df):,} geocoded ({overall_rate:.1%}) - "
          f"{len(donor_matched):,} from the GIS donor, {len(census_matched):,} from Census.")
    print("Report both figures in your methodology - failures are not random.")

    out.to_csv(BUSINESSES_GEOCODED_CSV, index=False)
    print(f"\nWrote {len(out):,} rows to {BUSINESSES_GEOCODED_CSV}")


if __name__ == "__main__":
    main()
