"""Authorship marks: small, invisible markers in the rendered map and every
app page that tie a copy back to this project.

    python scripts/fingerprint.py init                  # once: make the secret key (outside the repo)
    python scripts/fingerprint.py table                 # rewrite the committed checks table (needs the key)
    python scripts/fingerprint.py coverage              # the map and pages carry their marks (no key)
    python scripts/fingerprint.py verify <file or URL>  # is this copy ours? (needs the key)

A mark reads `lsc:v1:<id>:<check>`. The id is stable (`map/heatmap`,
`site`); the check is the first 16 hex digits of HMAC-SHA256(key, id). The
key is 32 random bytes kept outside the repository (KEY_FILE, or the path in
the LSC_KEY_FILE environment variable) and is never printed, committed or
pasted into a conversation. The checks are committed (FINGERPRINT_TABLE in
config.py), so any clone and any host render the same marks without the key.
Only `verify` needs it: a mark whose check matches could only have been made
by the key's holder, and git history dates it.

Never changes a coordinate, a count, a name or visible text, and never puts
an invisible character in text a reader copies. Marks are metadata only.

Verifying the live site: Streamlit builds its pages in the browser, so a
page URL returns only a loading shell with no marks. Save the page from a
browser ("Webpage, Complete") and verify the saved file, or verify
outputs/heatmap.html as served from GitHub.

Adapted from the expanded-heatmap project's kit (2026-10-04), with this
project's own prefix and key.
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import FINGERPRINT_PREFIX as PREFIX, FINGERPRINT_TABLE as TABLE, HEATMAP_HTML  # noqa: E402

KEY_ENV = "LSC_KEY_FILE"
KEY_FILE = Path(os.environ.get(KEY_ENV, Path.home() / ".lsc" / "fingerprint.key"))
PAGE_CODE = ROOT / "components.py"  # render_footer() draws the page mark

MARK = re.compile(re.escape(PREFIX) + r":([^:\"'<>\s]+):([0-9a-f]{16})")


def ids():
    """Every id a mark is made for: one map, and one mark shared by every
    page through the footer."""
    return ["site", "map/heatmap"]


def map_file(ident):
    return {"map/heatmap": HEATMAP_HTML}[ident]


def _key():
    if not KEY_FILE.exists():
        sys.exit(f"no key at {KEY_FILE}: run `python scripts/fingerprint.py init` on the owner's machine")
    return KEY_FILE.read_bytes()


def check_value(key, ident):
    return hmac.new(key, ident.encode("utf-8"), hashlib.sha256).hexdigest()[:16]


def cmd_init():
    if KEY_FILE.exists():
        print(f"key already present at {KEY_FILE} (left as is)")
        return
    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEY_FILE.write_bytes(secrets.token_bytes(32))
    print(f"key written to {KEY_FILE}. Back this file up somewhere private: "
          "without it no mark can be verified or made for a new item.")


def cmd_table():
    key = _key()
    table = {i: check_value(key, i) for i in ids()}
    TABLE.write_bytes((json.dumps(table, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(f"wrote {TABLE.relative_to(ROOT)}: {len(table)} marks")


def cmd_coverage():
    """No key needed: every id has a check in the table, the map file
    carries its mark, and the footer code draws the page mark."""
    problems = []
    table = json.loads(TABLE.read_text(encoding="utf-8")) if TABLE.exists() else {}
    want = ids()
    missing = [i for i in want if i not in table]
    if missing:
        problems.append(f"no mark in {TABLE.name} for: {', '.join(missing)} (run `table`)")
    for i in (i for i in want if i.startswith("map/")):
        text = map_file(i).read_text(encoding="utf-8", errors="replace")
        if not (table.get(i) and f"{PREFIX}:{i}:{table[i]}" in text):
            problems.append(f"{i}: no valid mark in {map_file(i).name} (re-run step 5)")
    if 'fingerprint_mark("site")' not in PAGE_CODE.read_text(encoding="utf-8"):
        problems.append(f"{PAGE_CODE.name} draws no page mark")
    if problems:
        print("FAIL:\n" + "\n".join("  " + p for p in problems))
        sys.exit(1)
    print("OK: the map and every page carry their marks.")


def cmd_verify(target):
    key = _key()
    if re.match(r"https?://", target):
        req = urllib.request.Request(target, headers={"User-Agent": "fingerprint verify"})
        text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    else:
        text = Path(target).read_text(encoding="utf-8", errors="replace")
    found = MARK.findall(text)
    if not found:
        print(f"no {PREFIX} mark found")
        sys.exit(1)
    for ident, check in sorted(set(found)):
        ok = hmac.compare_digest(check, check_value(key, ident))
        print(f"  {'VALID  ' if ok else 'INVALID'}  {ident}")


def main():
    args = sys.argv[1:]
    if args == ["init"]:
        cmd_init()
    elif args == ["table"]:
        cmd_table()
    elif args == ["coverage"]:
        cmd_coverage()
    elif len(args) == 2 and args[0] == "verify":
        cmd_verify(args[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
