"""Does every hand-typed number on the site still match outputs/?

Prose can't read a CSV, so the headline figures in the page write-ups are
typed by hand, and the same figure is often typed in several places (the
ring-1-to-4 fall appears on the Overview page and twice on the Findings
page). When the data changes, each copy has to be found and changed by
hand, and nothing fails if one is missed.

This check owns those numbers instead. FIGURES computes each one once, from
outputs/, formatted the way the site prints it. CITATIONS lists every place
a page types one, as the surrounding phrase with the figure left as a
{placeholder}. The check renders each phrase with the current values and
fails if the page text doesn't contain it.

Run:  python scripts/check_published_numbers.py

Needs only pandas - runs in the lean app venv, reads only outputs/ and the
page sources, never the network.

When it fails: the message names the file and the phrase it expected.
Either the data changed and the page is stale (change the number in the
page), or someone reworded the sentence (change the phrase in CITATIONS to
match the new wording, keeping the {placeholder}). Never "fix" it by
hardcoding the new number into FIGURES - that turns the check into a copy
of the page.

Adding a figure: compute it in figures(), then add one CITATIONS entry per
place it is typed. Search the pages for the formatted value first - a
figure cited in three places and registered in two is the defect this
exists to catch.

Rounding: once, half-up, from the unrounded value. Rounding a value that
was already printed rounded is how the site said 311 for a mean of 310.48
(310.48 -> 310.5 -> 311).
"""

import argparse
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

OVERVIEW = "Overview_&_Introduction.py"
FINDINGS = "pages/2_Findings_&_EDA.py"
METHODOLOGY = "pages/3_Methodology_&_Limitations.py"
FLOWCHART = "pages/4_Flowchart.py"

# (file, phrase). Phrases are matched after collapsing whitespace, so a
# sentence that wraps across source lines still matches.
CITATIONS = [
    (OVERVIEW, "drop {fall} between the innermost and outermost rings, {r1} to {r4}"),
    (OVERVIEW, "lands at r = {r}"),
    (OVERVIEW, "about {cv_ratio} times as uneven"),
    (OVERVIEW, "{chain_r1} in the first ring, and falls to {chain_r4} by the fourth"),

    (FINDINGS, "net decrease of -{fall} ({r1} businesses/sq mi → {r4})"),
    (FINDINGS, "({rise_2_3}) between rings 2 and 3"),
    (FINDINGS, "correlation (r={r})"),
    (FINDINGS, "{chain_brands} brands had at least two locations"),
    (FINDINGS, "accounting for {chain_share} of total businesses"),
    (FINDINGS, "reversal at the last ring ({chain_r3} to {chain_r4})"),
    (FINDINGS, "going from {chain_r1} share within concentric ring 1 down to {chain_r4} within ring 4"),
    (FINDINGS, "from ring 3 to 4 ({chain_rise_3_4})"),
    (FINDINGS, "Commercial density falls {fall} from the first ring to the last"),
    (FINDINGS, "commercial density at r = {r}"),

    (METHODOLOGY, "narrows {in_rings} pins"),
    # "Empty rings": the old values in that passage (957, 67.5%, +7.6%, 311)
    # describe the corrected error and are deliberately not checked.
    (METHODOLOGY, "drops from 957 to **{r1}** businesses/sq mi"),
    (METHODOLOGY, "decline goes from 67.5% to **{fall}**"),
    (METHODOLOGY, "shrinks from +7.6% to **{rise_2_3}**"),
    (METHODOLOGY, "the outermost ring averages {r4_exact}"),
    (METHODOLOGY, "**{overlap_brands} of {all_brands} ({overlap_pct})** touch"),
    (METHODOLOGY, "reported **{old_chain_share}** of locations as chains"),
    (METHODOLOGY, "**{chain_share} ({chain_brands} brands)**"),

    (FLOWCHART, "{citywide} geocoded"),
    (FLOWCHART, "({old_chain_share} -> {chain_share} of locations)"),
]

# Figures a page cites that cannot be derived from outputs/ - they need the
# raw export, the geo stack, or a rebuilt spatial join. Listed so they are a
# known gap rather than a forgotten one; check these by hand when the
# underlying data changes.
NOT_CHECKED = [
    "84,390 raw rows (Flowchart, Methodology) - data/raw, not outputs/",
    "41 withheld pins / 0.17% (Methodology) - step 5's name test",
    "1,767 (42.9%) multi-station claims (Methodology) - needs the spatial join",
    "8.7% to 8.4% without SODO/Stadium (Findings caption) - needs the join",
    "walking-trip percentages (Methodology) - cited literature, not data",
    "number words: 'sixteen stations', 'seven locations within a range of "
    "eight stations', 'five were in the top seven' (Findings)",
]


def half_up(x, places=0):
    """Conventional rounding. Python's round() is banker's: 310.5 -> 310."""
    q = Decimal(1).scaleb(-places)
    return Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP)


def pct(x, places=1):
    return f"{half_up(x * 100, places)}%"


def figures(root):
    out = root / "outputs"
    rings = pd.read_csv(out / "ring_stats.csv")
    stations = pd.read_csv(out / "station_stats.csv")
    chains = pd.read_csv(out / "chain_stats.csv")
    chain_ring = pd.read_csv(out / "chain_ring_stats.csv")
    coverage = pd.read_csv(out / "citywide_coverage.csv").iloc[0]

    # Same computation as Graph 1: mean density per ring across stations.
    gradient = rings.groupby("ring_index")["density_per_sq_mi"].mean().sort_index()
    r1, r2, r3, r4 = gradient.tolist()

    # Same as Graph 3 and Table 3.
    rides = stations["avg_monthly_boardings"]
    biz = stations["businesses_within_0_3mi"]
    cv = lambda s: s.std() / s.mean()  # noqa: E731

    # Same as the chain metrics on the Findings page.
    multi = chains[chains["location_count"] > 1]
    overlap = chains[(chains["location_count"] == 1) & (chains["station_count"] > 1)]
    old_def = chains[chains["station_count"] > 1]
    total_locs = chains["location_count"].sum()
    share = chain_ring.sort_values("ring")["chain_share"].tolist()

    return {
        "r1": f"{half_up(r1)}",
        "r4": f"{half_up(r4)}",
        "r4_exact": f"{half_up(r4, 2)}",
        "fall": pct(1 - r4 / r1),
        "rise_2_3": ("+" if r3 >= r2 else "") + pct(r3 / r2 - 1),
        "r": f"{half_up(biz.corr(rides), 3)}",
        "cv_ratio": f"{half_up(cv(biz) / cv(rides), 1)}",
        "chain_brands": f"{len(multi)}",
        "chain_share": pct(multi["location_count"].sum() / total_locs),
        "chain_r1": pct(share[0], 0),
        "chain_r3": pct(share[2]),
        "chain_r4": pct(share[3]),
        "chain_rise_3_4": ("+" if share[3] >= share[2] else "")
        + pct(share[3] - share[2]),
        "overlap_brands": f"{len(overlap):,}",
        "all_brands": f"{len(chains):,}",
        "overlap_pct": pct(len(overlap) / len(chains)),
        "old_chain_share": pct(old_def["location_count"].sum() / total_locs),
        "in_rings": f"{int(coverage['businesses_in_rings']):,}",
        "citywide": f"{int(coverage['businesses_citywide']):,}",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT,
                    help="project root (for testing against a copy)")
    root = ap.parse_args().root
    # The pages contain arrows and em dashes; the Windows console default
    # (cp1252) can't print them, which would crash the failure report.
    sys.stdout.reconfigure(encoding="utf-8")

    values = figures(root)
    print(f"{len(values)} figures computed from {root / 'outputs'}:")
    for k, v in values.items():
        print(f"   {k:18}{v}")

    texts, failures, used = {}, [], set()
    for rel, phrase in CITATIONS:
        path = root / rel
        if rel not in texts:
            if not path.exists():
                sys.exit(f"FAIL: {rel} does not exist. If it was renamed, "
                         "update the file constants at the top of this script.")
            texts[rel] = " ".join(path.read_text(encoding="utf-8").split())
        used.update(re.findall(r"\{(\w+)\}", phrase))
        expected = phrase.format(**values)
        if expected not in texts[rel]:
            failures.append((rel, expected))

    print(f"\n{len(CITATIONS)} citations checked across {len(texts)} files.")

    if not CITATIONS or not texts:
        sys.exit("FAIL: nothing was checked - CITATIONS is empty.")

    # A figure nobody cites is either a dead entry or, worse, a citation
    # that was deleted from CITATIONS while the page still types the number.
    unused = sorted(set(values) - used)
    if unused:
        sys.exit(f"FAIL: figures computed but never cited: {unused}. Search "
                 "the pages for their values and add a CITATIONS entry for "
                 "each place they appear, or delete them from figures().")

    print(f"{len(NOT_CHECKED)} cited figures are not derivable from outputs/ "
          "and are NOT checked here (see NOT_CHECKED).")

    if failures:
        print(f"\nFAIL: {len(failures)} citation(s) don't match the data.\n")
        for rel, expected in failures:
            print(f"   {rel}\n      expected to contain: {expected}")
        print("\nIf the data changed, update the number in that page. If the "
              "sentence was reworded, update its phrase in CITATIONS. Search "
              "the other pages for the old value too - it is rarely typed "
              "only once.")
        sys.exit(1)
    print("\nOK: every registered citation matches outputs/.")


if __name__ == "__main__":
    main()
