"""Which business names are a registrant's own identity, and so withheld.

One rule, shared by step 4 (chain_stats.csv), step 5 (the map's pins) and
scripts/check_personal_exposure.py (the gate that tests both). Kept out of
config.py for the reason given in rights.py; no page imports it.

A trade name chosen for a shop is commercial information, and publishing it
is the point of the project. A sole proprietor's own name is not, and the
registry publishes one wherever no trade name was filed. The test has two
halves, both load-bearing:

- The entity is a sole proprietorship, i.e. a natural person. Without this,
  single-member LLCs dominate, because an LLC's legal name is its brand
  ("Barking Gorgeous LLC"). An LLC filed under the owner's own name is
  deliberately not caught: that is a commercial identity chosen at filing.
- Every word of the published name appears in the legal name. Exact
  equality missed reordered names ("Jane Doe" against "DOE JANE M") and
  shortened ones ("Jane Doe" against "DOE JANE MARIE"). A published name
  that adds words to the owner's name ("Jane Doe Photography") is a chosen
  trade name and stays published, by the same reasoning as the LLC case.

Fails loudly rather than open: a missing column, or a registry export with
no sole proprietorships at all, raises instead of withholding nothing.
"""

import hashlib
import re

import pandas as pd

# Replaces a withheld name on the map and in chain_stats.csv. It states the
# reason so it reads as a deliberate omission, not missing data.
WITHHELD_NAME = "Name withheld (sole proprietor)"

PUBLISHED_COL = "business_name"
LEGAL_COL = "Business Legal Name"
OWNERSHIP_COL = "Ownership Type"
REQUIRED_COLUMNS = (PUBLISHED_COL, LEGAL_COL, OWNERSHIP_COL)
SOLE_PROPRIETOR = "Sole proprietorship"

# Entity suffixes and articles carry no identity. Single letters are dropped
# too: they are middle initials ("DOE JANE M"), which a published name
# usually leaves out.
_IGNORED_WORDS = re.compile(r"\b(?:LLC|INC|CORP|CO|LTD|LP|LLP|PLLC|THE)\b")


def name_words(name) -> frozenset:
    """The identifying words of a name, ignoring case, punctuation and order."""
    if not isinstance(name, str):
        return frozenset()
    s = re.sub(r"[^A-Z0-9 ]", " ", name.upper())
    s = _IGNORED_WORDS.sub(" ", s)
    return frozenset(w for w in s.split() if len(w) > 1)


def require_columns(df):
    """Raise if the registry columns the rule needs are absent or renamed."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(
            f"Name withholding needs columns {missing}, absent from the data. "
            "A renamed registry column would otherwise withhold nothing.")
    ownership = df[OWNERSHIP_COL].fillna("").str.strip()
    if len(df) and not (ownership == SOLE_PROPRIETOR).any():
        raise ValueError(
            f"No {OWNERSHIP_COL!r} value equals {SOLE_PROPRIETOR!r}. The "
            "category was probably renamed in the registry export; update "
            "SOLE_PROPRIETOR in withholding.py.")


def own_identity_mask(df) -> pd.Series:
    """True where a row's published name is its registrant's own identity."""
    require_columns(df)
    is_person = df[OWNERSHIP_COL].fillna("").str.strip() == SOLE_PROPRIETOR
    published = df[PUBLISHED_COL].map(name_words)
    legal = df[LEGAL_COL].map(name_words)
    contained = pd.Series(
        [bool(p) and p <= l for p, l in zip(published, legal)], index=df.index)
    return is_person & contained


def withheld_keys(df, key) -> set:
    """Comparison keys (e.g. normalized brands) of every own-identity name.

    A name withheld on one row is withheld on every row sharing its key, so
    the same string never survives elsewhere in the same output.
    """
    keys = set(df.loc[own_identity_mask(df), PUBLISHED_COL].map(key))
    keys.discard("")
    return keys


def withhold_mask(df, key) -> pd.Series:
    """Rows to withhold: own-identity rows plus any row sharing their key."""
    return df[PUBLISHED_COL].map(key).isin(withheld_keys(df, key))


def placeholder_labels(keys) -> dict:
    """Map each withheld key to a distinct numbered placeholder.

    Distinct, so grouping by the placeholder counts exactly as grouping by
    the name did. Numbered in hash order rather than alphabetical order, so
    the numbering carries nothing about the names.
    """
    ordered = sorted(keys, key=lambda k: hashlib.sha256(k.encode("utf-8")).hexdigest())
    return {k: f"{WITHHELD_NAME} {i}" for i, k in enumerate(ordered, 1)}
