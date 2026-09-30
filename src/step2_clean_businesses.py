"""Step 2: clean the Seattle business license export.

Input:  data/raw/business_licenses.csv
Output: data/processed/businesses_clean.csv

Cleaning runs before geocoding because geocoding is the slow step: every
row dropped here is one fewer to geocode.

COLUMN_MAP maps the export's headers to the names used downstream.
Seattle's schema has changed across releases, so re-check it against the
headers this script prints whenever the export is re-downloaded.

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
    NAICS_STOREFRONT_EXCLUDE,
)

RAW_CSV = DATA_RAW / "business_licenses.csv"

# Mapped against "Active Business License Tax Certificate" (data.seattle.gov
# wnbq-64tb), downloaded 2026-09-06. Headers confirmed against the raw file.
COLUMN_MAP = {
    "business_name": "Trade Name",
    "ubi": "UBI",                       # 8.3% blank, so not used for dedupe
    "naics": "NAICS Code",
    "street": "Street Address",
    "city": "City",
    "state": "State",
    "zip": "Zip",
    "status": None,                     # no status/expiration column: active-only snapshot
    "account_number": "City Account Number",  # 0% blank, 0 dupes: the real dedupe key,
                                               # and the join key to the GIS geometry donor in step 3
    "license_start_date": "License Start Date",  # YYYYMMDD string; feeds the tenure analysis in step 4
}

# This export mixes Seattle addresses with businesses that hold a Seattle tax
# certificate but are located elsewhere (Kent, Bellevue, Tacoma, ...), about
# 30% of rows. Restrict to Seattle before any other filtering.
CITY_KEEP = "SEATTLE"

# "19000101" is a null-date placeholder in this export, not a real founding
# date. Left in, it would add a supposedly 126-year-old business to the
# tenure calculation. Nulled in main(), not dropped: the rest of the row is
# fine.
SENTINEL_LICENSE_START_DATE = "19000101"


def normalize_address(street: str) -> str:
    """Strip unit designators and standardize spacing.

    Suite and unit fragments are the main cause of geocoder misses. Seattle's
    directional suffixes (N, NE, S, SW, W) matter and are deliberately kept.

    The `usaddress` library parses a street string into components for
    harder cases. It wasn't needed here (99.5% geocoded overall), so it is
    not in requirements-pipeline.txt.
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

    # Read everything as strings: ZIPs read as integers silently lose ZIP+4
    # values and leading zeros.
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

    # --- Small per-field data-quality fixes -------------------------------
    # Fixed here, at the source, rather than worked around downstream. See
    # docs/DECISIONS.md "Open items".
    blank_name = df["business_name"].fillna("").str.strip() == ""
    if blank_name.any():
        print(f"Filling {blank_name.sum()} blank Trade Name(s) from Business Legal Name")
        df.loc[blank_name, "business_name"] = df.loc[blank_name, "Business Legal Name"]

    sentinel = df["license_start_date"] == SENTINEL_LICENSE_START_DATE
    if sentinel.any():
        print(
            f"Nulling {sentinel.sum()} sentinel license_start_date value(s) "
            f"({SENTINEL_LICENSE_START_DATE!r} is a null-date placeholder, "
            "not a real founding date)"
        )
        df.loc[sentinel, "license_start_date"] = ""
    print()

    # --- Restrict to Seattle ----------------------------------------------
    # First, so the drop counts below describe Seattle businesses only, not
    # a mix including Kent/Bellevue/Tacoma businesses with a Seattle license.
    before = len(df)
    df = df[df["city"].str.upper().str.strip() == CITY_KEEP]
    print(f"Seattle filter: {before:,} -> {len(df):,} rows")

    # --- Filter to storefront categories --------------------------------
    # The most consequential choice in the script: everything downstream
    # inherits it. The prefix list is NAICS_STOREFRONT_PREFIXES in config.py.
    before = len(df)
    naics = df["naics"].fillna("").astype(str)
    keep = naics.str.startswith(tuple(NAICS_STOREFRONT_PREFIXES))
    df = df[keep]
    print(f"NAICS filter: {before:,} -> {len(df):,} rows")

    # --- Drop individually-excluded categories ---------------------------
    # Codes whose prefix matched above but that don't belong, each for a
    # specific reason. The reasoning lives in NAICS_STOREFRONT_EXCLUDE in
    # config.py, which the Methodology page also renders.
    if NAICS_STOREFRONT_EXCLUDE:
        before = len(df)
        excluded = naics[df.index].isin(NAICS_STOREFRONT_EXCLUDE)
        for code, (label, _reason) in NAICS_STOREFRONT_EXCLUDE.items():
            n = (naics[df.index] == code).sum()
            print(f"  excluding {code} ({label}): {n:,} rows")
        df = df[~excluded]
        print(f"NAICS exclusions: {before:,} -> {len(df):,} rows")

    # --- Active licenses only -------------------------------------------
    # A dataset of currently-active licenses only has no record of closures,
    # and so no survival denominator. That is a documented limitation, not
    # something to work around silently.
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
    # One physical location can hold several licenses. Dedupe on City
    # Account Number plus normalized address: not UBI (8.3% blank), and
    # never business name alone, since chains share names.
    df["street_clean"] = df["street"].apply(normalize_address)
    before = len(df)
    df = df.drop_duplicates(subset=["account_number", "street_clean"])
    print(f"Deduplication: {before:,} -> {len(df):,} rows")

    # --- Drop unusable addresses ----------------------------------------
    before = len(df)
    df = df[df["street_clean"].str.len() > 0]
    df = df[~df["street_clean"].str.contains("PO BOX|P O BOX", na=False)]
    print(f"Address validity: {before:,} -> {len(df):,} rows")

    # The Census geocoder needs a unique id per row.
    df = df.reset_index(drop=True)
    df["record_id"] = df.index.astype(str)

    BUSINESSES_CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(BUSINESSES_CLEAN_CSV, index=False)
    print(f"\nWrote {len(df):,} rows to {BUSINESSES_CLEAN_CSV}")


if __name__ == "__main__":
    main()
