"""No em dashes in comments. A hard rule for this project.

Covers every kind of comment in the project's Python files:

- `#` comments
- docstrings
- comments embedded in string literals: CSS `/* */`, JavaScript `//`, and
  HTML `<!-- -->` (the pages and the map carry CSS and JS as strings, and
  those comments ship to the browser)

Visible text is out of scope: an em dash in a label, caption or page
prose is a design choice, not a comment (the map's layer names use them).

Run:  python scripts/check_no_em_dashes.py

Needs nothing beyond the standard library. When it fails, reword the
listed comment with a colon, semicolon, comma, parentheses, or a plain
hyphen. Don't swap in an en dash or a double hyphen to get around it.
"""

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EM_DASH = "—"

# Comments embedded in string literals. The `//` pattern skips "://" so a
# URL isn't read as the start of a JavaScript comment.
EMBEDDED = re.compile(r"/\*.*?\*/|<!--.*?-->|(?<![:\w])//[^\n]*", re.S)


def project_files(root):
    top = [root / "config.py", root / "components.py", root / "Overview_&_Introduction.py"]
    rest = [p for d in ("pages", "src", "scripts") for p in sorted((root / d).glob("*.py"))]
    return [p for p in top + rest if p.exists()]


def docstring_nodes(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                yield body[0].value


def scan(path):
    """Returns (hits, counts). hits: [(line, kind, text)]."""
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    hits, counts = [], {"comment": 0, "docstring": 0, "embedded": 0}

    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            counts["comment"] += 1
            if EM_DASH in tok.string:
                hits.append((tok.start[0], "comment", tok.string.strip()))

    docstrings = set()
    for node in docstring_nodes(tree):
        docstrings.add(id(node))
        counts["docstring"] += 1
        for i, line in enumerate(node.value.splitlines()):
            if EM_DASH in line:
                hits.append((node.lineno + i, "docstring", line.strip()))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                and id(node) not in docstrings:
            for m in EMBEDDED.finditer(node.value):
                counts["embedded"] += 1
                if EM_DASH in m.group(0):
                    line = node.lineno + node.value[:m.start()].count("\n")
                    hits.append((line, "embedded comment", " ".join(m.group(0).split())[:100]))
    return hits, counts


def main():
    ap_root = Path(sys.argv[sys.argv.index("--root") + 1]) if "--root" in sys.argv else ROOT
    sys.stdout.reconfigure(encoding="utf-8")
    files = project_files(ap_root)
    if not files:
        sys.exit(f"FAIL: found no project .py files under {ap_root}.")

    total = {"comment": 0, "docstring": 0, "embedded": 0}
    failures = []
    for path in files:
        hits, counts = scan(path)
        for k in total:
            total[k] += counts[k]
        failures += [(path.relative_to(ap_root), *h) for h in hits]

    print(f"Scanned {len(files)} files: {total['comment']} # comments, "
          f"{total['docstring']} docstrings, {total['embedded']} CSS/JS/HTML "
          "comments inside strings.")
    if not total["comment"]:
        sys.exit("FAIL: found no comments at all - the scan is broken.")

    if failures:
        print(f"\nFAIL: {len(failures)} em dash(es) in comments.\n")
        for rel, line, kind, text in sorted(failures):
            print(f"   {rel}:{line} ({kind}): {text}")
        print("\nReword each with a colon, semicolon, comma, parentheses or a "
              "plain hyphen.")
        sys.exit(1)
    print("OK: no em dashes in any comment or docstring.")


if __name__ == "__main__":
    main()
