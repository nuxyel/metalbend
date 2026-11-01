"""The BendHub packages the corpus imports, with what is installed for each: one line per package, for env.tsv.

    python3 -I scripts/packages.py            # pkg_<name>@<version>\t<store id> <content hash>

Reads the import lines of workloads/*/*.bend and lib/*.bend, then those of each package, so a package that another
imports is listed too. A package's store id is Bend's (BEND_LIB, ~/.bend/lib by default: names/<name>@<version> holds
it); its content hash is the first 16 hex digits of a SHA-256 over its files' paths and bytes, so a package changed
in the store under the same version shows. A package that is not installed is listed as `missing`.
"""
import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMPORT = re.compile(r"^import\s+([A-Za-z0-9_.-]+@[0-9][0-9.]*)/", re.M)


def imports(path):
    try:
        return IMPORT.findall(Path(path).read_text())
    except OSError:
        return []


def content_hash(d):
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file()):
        h.update(str(f.relative_to(d)).encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


def packages(root=ROOT, lib=None):
    lib = Path(lib or os.environ.get("BEND_LIB") or Path.home() / ".bend" / "lib")
    todo = [p for f in sorted(root.glob("workloads/*/*.bend")) + sorted(root.glob("lib/*.bend")) for p in imports(f)]
    seen = {}
    while todo:
        p = todo.pop()
        if p in seen:
            continue
        name = lib / "names" / p
        if not name.is_file():
            seen[p] = "missing"
            continue
        sid = name.read_text().strip()
        d = lib / sid
        seen[p] = f"{sid} {content_hash(d)}" if d.is_dir() else f"{sid} missing"
        todo += imports(d / "main.bend")
    return dict(sorted(seen.items()))


def main():
    for p, v in packages().items():
        print(f"pkg_{p}\t{v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
