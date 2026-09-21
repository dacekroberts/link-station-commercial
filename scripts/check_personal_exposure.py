"""Pre-publish check: is the map about to publish people's names at their homes?

The heatmap plots every in-ring business as a pin carrying its `business_name`
at a geocoded street address. A trade name someone chose for their shop is
commercial information and mapping it is the point. A sole proprietor's own
name at their house is not, even though the registry holding it is public: a
registry entry sits behind a search box, a map pin is a plotted coordinate.

This prints numbers, deliberately not a pass/fail. The judgment is a person's.
A check that prints a verdict nobody reads is worse than one that prints
numbers somebody has to think about.

Run:  python scripts/check_personal_exposure.py

Needs the pipeline venv (geopandas) and the local `data/` tree, so this is a
developer gate, not something the deployed app runs. Re-run it after any
change to row filtering (step 2) or classification, since both change which
rows reach the map.

The zoning layer is an optional input and is NOT a pipeline dependency - the
project does not ship it, and nothing in `outputs/` derives from it. Without
it the check still runs, minus the strongest signal. To fetch it:

    https://services.arcgis.com/ZOyb2t4B0UYuYNYH/arcgis/rest/services
        /Current_Land_Use_Zoning_Detail_2/FeatureServer/0/query
        ?where=1=1&outFields=ZONING,BASE_ZONE,CLASS_DESC,CATEGORY_DESC
        &outSR=4326&f=geojson&resultOffset=0&resultRecordCount=2000

  paged at 2000 (the service caps there; 3,627 polygons as of 2026-09-20),
  concatenated into data/raw/seattle_zoning.geojson. Source: City of Seattle
  "Current Land Use Zoning Detail" on Seattle GeoData.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (  # noqa: E402
    DATA_RAW,
    STATIONS_CSV,
    BUSINESSES_GEOCODED_CSV,
    CRS_GEOGRAPHIC,
    CRS_PROJECTED,
    RING_EDGES_METERS,
)

RAW_CSV = DATA_RAW / "business_licenses.csv"
ZONING_GEOJSON = DATA_RAW / "seattle_zoning.geojson"
FLAGGED_CSV = Path(__file__).parent.parent / "personal_exposure_flagged.csv"

# Seattle's registry column names. TRADE is what the map publishes; OWNER is
# what step 2 falls back to when TRADE is blank, and is the registrant.
TRADE_COL = "Trade Name"
OWNER_COL = "Business Legal Name"

# Tokens that mark a name as a business rather than a person. Deliberately
# generous: a false "this is a business" only ever makes the check report
# LESS exposure than exists, and the floor below is already the real problem.
BUSINESS_TOKENS = re.compile(
    r"\b(?:LLC|L\.?L\.?C|INC|CORP|CO|LTD|LP|LLP|PLLC|COMPANY|SERVICES?|SALON"
    r"|SHOP|STORE|STUDIO|CENTER|CENTRE|GROUP|SOLUTIONS|ENTERPRISES|CONSULTING"
    r"|DESIGN|MARKET|CAFE|COFFEE|SPA|CLEANERS|LAUNDRY|REPAIR|SUPPLY|TRADING"
    r"|IMPORTS|GALLERY|BOUTIQUE|WORKS|MEDIA|PRODUCTIONS|PROPERTIES|HOLDINGS"
    r"|PARTNERS|ASSOCIATES|INTERNATIONAL|GLOBAL|NORTHWEST|SEATTLE|PUGET|SOUND)\b"
)

# Zoning classes that mean people live there. "Multi-Family" is included but
# reported separately: lowrise multi-family carries plenty of legitimate
# ground-floor commercial, so it is a weaker signal than single-family.
SINGLE_FAMILY = "Neighborhood Residential"
MULTI_FAMILY = "Multi-Family"


def normalize(name) -> str:
    """Strip punctuation and entity suffixes so two spellings compare equal."""
    if not isinstance(name, str):
        return ""
    s = re.sub(r"[^A-Z0-9 ]", " ", name.upper())
    s = re.sub(r"\b(?:LLC|INC|CORP|CO|LTD|LP|LLP|PLLC|THE)\b", " ", s)
    return " ".join(s.split())


def own_identity(row) -> bool:
    """Is the published name the registrant's own identity, not a trade name?

    Two conditions, and both matter:

    - The published name equals the legal entity name. Someone who picked a
      trade name has two different strings here; someone who never picked one
      is published under whatever the registry holds, which for a natural
      person is their name.
    - The entity is a sole proprietorship, i.e. a natural person. Without
      this, single-member LLCs dominate the result, because an LLC's legal
      name IS its brand - "Barking Gorgeous LLC" and "Blue Sky Bridal" both
      match the first condition and neither is anybody's personal name.

    This is the signal that separates the two cases the name regex cannot:
    a name someone chose to trade under, versus a name the registry is
    exposing on their behalf. It deliberately does NOT flag a person who
    registered an LLC under their own name ("Anne McGowan LLC") - that is a
    commercial identity they chose to file.
    """
    published = normalize(row.get("business_name"))
    legal = normalize(row.get("Business Legal Name"))
    is_sole = str(row.get("Ownership Type", "")).strip() == "Sole proprietorship"
    return bool(published) and published == legal and is_sole


def person_like(name) -> bool:
    """Two or three capitalised words, no corporate token, no digits or '&'.

    Noisy on purpose-built trade names: "Haute Tip", "Gear By Julian" and
    "What's Your Mood" all pass. See the floor this produces, printed below -
    it is around 43% of every pin, in every zone, so this signal is close to
    worthless on its own and is only meaningful intersected with zoning.
    """
    if not isinstance(name, str):
        return False
    s = name.upper()
    if any(c.isdigit() for c in s) or "&" in s:
        return False
    if BUSINESS_TOKENS.search(s):
        return False
    return 2 <= len(s.split()) <= 3


def published_pins():
    """The businesses the map actually draws: those inside some station ring.

    Same nearest-station distance test step5_map.py uses to pick its pin set,
    not step4's overlap-aware spatial join - this asks "what is on the map",
    which is the population the privacy question is about.
    """
    import geopandas as gpd

    geo = pd.read_csv(BUSINESSES_GEOCODED_CSV, dtype=str).reset_index(drop=True)
    stations = pd.read_csv(STATIONS_CSV)

    def gdf(df):
        return gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(df["longitude"].astype(float),
                                        df["latitude"].astype(float)),
            crs=CRS_GEOGRAPHIC,
        ).to_crs(CRS_PROJECTED)

    biz, sta = gdf(geo), gdf(stations)
    bxy = np.column_stack([biz.geometry.x, biz.geometry.y])
    sxy = np.column_stack([sta.geometry.x, sta.geometry.y])
    nearest = np.sqrt(((bxy[:, None, :] - sxy[None, :, :]) ** 2).sum(-1)).min(1)
    return biz[nearest <= RING_EDGES_METERS[-1]].copy()


def check_fallback(pub):
    """Did step 2's blank-trade-name fallback put a registrant on the map?

    Measured against the RAW export, never the processed intermediate: step 2
    renames the trade column and fills its blanks in the same pass, so the
    processed file's blank count reads as zero whether or not the fallback
    fired. Only the raw export still knows.
    """
    raw = pd.read_csv(RAW_CSV, dtype=str, low_memory=False)
    trade = raw[TRADE_COL].fillna("").str.strip()
    owner = raw[OWNER_COL].fillna("").str.strip()
    fallback_only = (set(owner[(trade == "") & (owner != "")].str.upper())
                     - set(trade[trade != ""].str.upper()))
    hits = pub[pub["business_name"].fillna("").str.upper().isin(fallback_only)]

    print("1. DID THE FALLBACK FIRE?")
    print(f"   raw rows with a blank {TRADE_COL!r}: "
          f"{(trade == '').sum():,} of {len(raw):,} ({(trade == '').mean() * 100:.3f}%)")
    print(f"   distinct names only explicable as the {OWNER_COL!r} fallback: "
          f"{len(fallback_only):,}")
    print(f"   >> published pins traceable to it: {len(hits)} "
          f"({len(hits) / len(pub) * 100:.3f}%)")
    return hits


def check_zoning(pub):
    """Intersect a person-like name with land that people live on."""
    import geopandas as gpd

    print("\n2. PERSON-LIKE NAME x ZONING")
    pub["person"] = pub["business_name"].apply(person_like)
    floor = pub["person"].mean()
    print(f"   person-like across ALL pins (the false-positive floor): "
          f"{pub['person'].sum():,} ({floor * 100:.1f}%)")

    if not ZONING_GEOJSON.exists():
        print(f"   no zoning layer at {ZONING_GEOJSON} - skipping the zoning")
        print("   intersection. See this file's docstring for how to fetch it.")
        print("   Without it, the name heuristic alone tells you almost nothing.")
        return None

    zones = gpd.read_file(ZONING_GEOJSON).to_crs(CRS_PROJECTED)
    joined = gpd.sjoin(pub, zones[["CLASS_DESC", "geometry"]],
                       how="left", predicate="within")
    joined = joined[~joined.index.duplicated(keep="first")]
    matched = joined["CLASS_DESC"].notna().mean()
    print(f"   pins matched to a zone: {joined['CLASS_DESC'].notna().sum():,} "
          f"({matched * 100:.1f}%)")

    print(f"\n   {'zone class':40}{'pins':>7}{'person-like':>13}{'rate':>9}")
    for cls, sub in sorted(joined.groupby("CLASS_DESC"),
                           key=lambda kv: -len(kv[1])):
        rate = sub["person"].mean()
        print(f"   {cls:40}{len(sub):>7}{sub['person'].sum():>13}{rate * 100:>8.1f}%")

    # The number that matters is not the count in residential zones - it is
    # whether the person-like RATE is meaningfully higher there than in
    # obviously commercial zones. If it is not, the count is just the floor
    # above, redistributed, and says nothing about people's homes.
    resid = joined[joined["CLASS_DESC"].isin([SINGLE_FAMILY, MULTI_FAMILY])]
    comm = joined[joined["CLASS_DESC"].isin(["Downtown", "Commercial/Mixed Use"])]
    flagged = resid[resid["person"]]
    print(f"\n   >> person-like AND residentially zoned: {len(flagged)} "
          f"({len(flagged) / len(joined) * 100:.2f}% of all pins)")
    if len(comm):
        print(f"   person-like rate, residential zones : {resid['person'].mean() * 100:.1f}%")
        print(f"   person-like rate, commercial zones  : {comm['person'].mean() * 100:.1f}%")
        print(f"   difference over the floor           : "
              f"{(resid['person'].mean() - comm['person'].mean()) * 100:+.1f} points")
        print("   A small difference means the count above is mostly the")
        print("   heuristic's own noise, not evidence of home addresses.")

    # The signal that actually answers the question. See own_identity().
    print("\n3. IS THE PUBLISHED NAME THE REGISTRANT'S OWN IDENTITY?")
    joined["own_identity"] = joined.apply(own_identity, axis=1)
    mine = joined[joined["own_identity"]]
    on_res = joined[joined["own_identity"] & joined["CLASS_DESC"].isin(
        [SINGLE_FAMILY, MULTI_FAMILY])]
    on_sf = joined[joined["own_identity"] & (joined["CLASS_DESC"] == SINGLE_FAMILY)]
    print(f"   published name == legal name AND a sole proprietorship: "
          f"{len(mine)} ({len(mine) / len(joined) * 100:.2f}%)")
    print(f"   >> of those, on residentially zoned land: {len(on_res)} "
          f"({len(on_res) / len(joined) * 100:.2f}%)")
    print(f"   >> of those, on single-family land:       {len(on_sf)} "
          f"({len(on_sf) / len(joined) * 100:.2f}%)")
    print("   This set is small enough to read in full, and it is the one")
    print("   worth reading: it excludes trade names by construction rather")
    print("   than by guessing at them.")
    if len(on_res):
        print()
        for _, r in on_res.iterrows():
            print(f"      {str(r['business_name'])[:34]:36}{str(r['naics']):8}"
                  f"{str(r['CLASS_DESC'])}")
    return on_res


def main():
    for path in (RAW_CSV, BUSINESSES_GEOCODED_CSV, STATIONS_CSV):
        if not path.exists():
            sys.exit(f"Missing {path}. Run the pipeline first.")

    pub = published_pins()
    print(f"Published map pins (inside some station ring): {len(pub):,}\n")

    fallback_hits = check_fallback(pub)
    flagged = check_zoning(pub)

    # Guard the empty case explicitly: with no zoning layer present and a
    # clean fallback, both frames are empty and pd.concat([]) raises. That is
    # the default path on a fresh clone, so it must not look like a crash.
    parts = [f for f in (fallback_hits, flagged) if f is not None and len(f)]
    if parts:
        out = pd.concat(parts)
        cols = [c for c in ["business_name", "naics", "street", "CLASS_DESC"]
                if c in out.columns]
        out = out[cols].drop_duplicates()
        out.to_csv(FLAGGED_CSV, index=False, encoding="utf-8-sig")
        print(f"\nWrote {len(out):,} flagged rows to {FLAGGED_CSV.name} "
              "for hand review.")
    else:
        print("\nNothing flagged by the signals that ran.")

    print("\nLimits, which belong in anything written from this: the name test")
    print("is a regex and cannot tell a real shop trading under its owner's")
    print("name from a registrant at home. Zoning is permitted use, not actual")
    print("use. No row here is individually verified and nobody was contacted.")
    print("Record the numbers, the date and the decision, so a later reader can")
    print("re-judge it rather than trust it.")


if __name__ == "__main__":
    main()
