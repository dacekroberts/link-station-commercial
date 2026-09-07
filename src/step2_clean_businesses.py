"""Step 2 - Clean the Seattle business license export.

Input:  data/raw/business_licenses.csv
Output: data/processed/businesses_clean.csv

Cleaning happens before geocoding for a reason: geocoding is the slow step,
and every row you drop here is a row you do not pay for later.

The column names below are placeholders. Open the raw CSV first, look at
the actual headers, and fill in COLUMN_MAP. Seattle's schema has changed
across releases and this script cannot guess it.

Run:  python src/step2_clean_businesses.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    BUSINESSES_CLEAN_CSV,
    NAICS_STOREFRONT_PREFIXES,
)

RAW_CSV = DATA_RAW / "business_licenses.csv"

# TODO: fill these in after inspecting the raw file's headers.
COLUMN_MAP = {
    "business_name": "TODO",
    "ubi": "TODO",          # unique business identifier, for deduplication
    "naics": "TODO",
    "street": "TODO",
    "city": "TODO",
    "state": "TODO",
    "zip": "TODO",
    "status": "TODO",       # may not exist - see note in main()
}


def normalize_address(street: str) -> str:
    """Strip unit designators and standardise spacing.

    Suite and unit fragments are the main cause of geocoder misses. Seattle's
    directional suffixes (N, NE, S, SW, W) matter and are deliberately kept.

    For harder cases, the `usaddress` library parses a string into components
    and is worth reaching for if your match rate comes back poor.
    """
    if not isinstance(street, str):
        return ""
    s = street.upper().strip()
    for marker in (" STE ", " SUITE ", " UNIT ", " APT ", " #", " RM ", " FL "):
        if marker in s:
            s = s.split(marker)[0]
    return " ".join(s.split())


def main():
    if not RAW_CSV.exists():
        sys.exit(
            f"No file at {RAW_CSV}.\n"
            "Download the active business license export from Seattle's open "
            "data portal. See data/raw/README.md."
        )

    # Always read ZIPs as strings. Reading them as integers silently mangles
    # ZIP+4 values and any code with a leading zero.
    df = pd.read_csv(RAW_CSV, dtype=str, low_memory=False)

    print(f"Loaded {len(df):,} rows")
    print("\nColumns in this file:")
    for c in df.columns:
        print(f"  {c}")
    print()

    if "TODO" in COLUMN_MAP.values():
        sys.exit(
            "COLUMN_MAP still has TODO entries. Map them to the column names "
            "printed above, then re-run."
        )

    df = df.rename(columns={v: k for k, v in COLUMN_MAP.items()})

    # --- Filter to storefront categories --------------------------------
    # This is the single most consequential choice in the script. Everything
    # downstream inherits it. Record the prefix list in your methodology.
    before = len(df)
    naics = df["naics"].fillna("").astype(str)
    keep = naics.str.startswith(tuple(NAICS_STOREFRONT_PREFIXES))
    df = df[keep]
    print(f"NAICS filter: {before:,} -> {len(df):,} rows")

    # --- Active licenses only -------------------------------------------
    # If this dataset holds only currently-active licenses, you have no
    # record of closures and therefore no survival denominator. That is a
    # documented limitation, not something to work around silently.
    if "status" in df.columns and df["status"].notna().any():
        print(f"\nStatus values present: {df['status'].value_counts().to_dict()}")
        print("Filter to active rows here if the column supports it.")
    else:
        print(
            "\nNOTE: no usable status column. This export is likely a snapshot "
            "of active licenses only. Tenure figures will describe survivors, "
            "not survival. Say so on the methodology page."
        )

    # --- Deduplicate ----------------------------------------------------
    # One physical location can hold several licenses. Dedupe on UBI plus
    # normalized address, never on business name - chains share names.
    df["street_clean"] = df["street"].apply(normalize_address)
    before = len(df)
    df = df.drop_duplicates(subset=["ubi", "street_clean"])
    print(f"Deduplication: {before:,} -> {len(df):,} rows")

    # --- Drop unusable addresses ----------------------------------------
    before = len(df)
    df = df[df["street_clean"].str.len() > 0]
    df = df[~df["street_clean"].str.contains("PO BOX|P O BOX", na=False)]
    print(f"Address validity: {before:,} -> {len(df):,} rows")

    # The Census geocoder wants a unique id per row.
    df = df.reset_index(drop=True)
    df["record_id"] = df.index.astype(str)

    BUSINESSES_CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(BUSINESSES_CLEAN_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {BUSINESSES_CLEAN_CSV}")


if __name__ == "__main__":
    main()
