"""Step 3 - Geocode addresses with the Census bulk geocoder.

Input:  data/processed/businesses_clean.csv
Output: data/processed/businesses_geocoded.csv

The Census Bulk Geocoder is free, needs no API key, and takes CSV in and CSV
out. It accepts 10,000 rows per request, so this batches.

Its required input format is positional and headerless:

    unique_id, street, city, state, zip

Batches are cached to data/raw/geocode_cache/. Re-running skips completed
batches, so a timeout partway through costs you one batch, not the run.

Run:  python src/step3_geocode.py
"""

import sys
import time
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    BUSINESSES_CLEAN_CSV,
    BUSINESSES_GEOCODED_CSV,
    KING_COUNTY_BBOX,
)

GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE = 5000       # under the 10k ceiling; smaller batches fail less often
CACHE_DIR = DATA_RAW / "geocode_cache"

RESULT_COLUMNS = [
    "record_id", "input_address", "match_status", "match_type",
    "matched_address", "coordinates", "tiger_line_id", "side",
]


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


def main():
    if not BUSINESSES_CLEAN_CSV.exists():
        sys.exit(f"Run step2_clean_businesses.py first - no {BUSINESSES_CLEAN_CSV}")

    df = pd.read_csv(BUSINESSES_CLEAN_CSV, dtype=str)
    print(f"Geocoding {len(df):,} addresses in batches of {BATCH_SIZE}\n")

    results = []
    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i + BATCH_SIZE]
        results.append(geocode_batch(batch, i // BATCH_SIZE))
        time.sleep(1)

    geo = pd.concat(results, ignore_index=True)

    # The geocoder returns "lon,lat" in one field. Note the order.
    matched = geo[geo["match_status"] == "Match"].copy()
    coords = matched["coordinates"].str.split(",", expand=True)
    matched["longitude"] = pd.to_numeric(coords[0], errors="coerce")
    matched["latitude"] = pd.to_numeric(coords[1], errors="coerce")

    match_rate = len(matched) / len(df) if len(df) else 0
    print(f"\nMatch rate: {match_rate:.1%} ({len(matched):,} of {len(df):,})")
    print("Report this figure in your methodology - failures are not random.")
    if match_rate < 0.80:
        print(
            "\nBelow 80%. Usually address formatting. Try the `usaddress` "
            "library in step 2 to parse street strings into components."
        )

    # Sanity bounds. Catches swapped lat/lon and wild mismatches.
    before = len(matched)
    b = KING_COUNTY_BBOX
    matched = matched[
        matched["latitude"].between(b["lat_min"], b["lat_max"])
        & matched["longitude"].between(b["lon_min"], b["lon_max"])
    ]
    if before != len(matched):
        print(f"Dropped {before - len(matched)} points outside King County bounds")

    out = df.merge(
        matched[["record_id", "latitude", "longitude", "match_type"]],
        on="record_id",
        how="inner",
    )
    out.to_csv(BUSINESSES_GEOCODED_CSV, index=False)
    print(f"\nWrote {len(out):,} rows to {BUSINESSES_GEOCODED_CSV}")


if __name__ == "__main__":
    main()
