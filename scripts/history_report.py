"""The history's report: every workload's Cachegrind counts over a range of Bend releases (scripts/history.sh's rows,
a workload's releases all counted on one machine), compared release by release.

    python3 -I scripts/history_report.py <folder>     # reads <folder>/counts.tsv and gaps.tsv

Each step from a release to the next is judged as the release watch judges two Bends (scripts/track_verdict.py:
instructions beyond 0.1%, simulated D1 misses beyond 5%, an output that is not its oracle), with two more verdicts:
gap (the workload builds on neither release) and first (it builds on the new one only, its first count). Writes
steps.tsv (one row per workload and step), coverage.tsv (one row per workload, one column per release: ok, or why
not) and report.md (per release: how many workloads got faster, slower or stayed the same, the biggest moves; per
workload: its change from its first release to its last). Prints the per-release table. Exits 0, or 2 on a bad
folder.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from track_verdict import change, judge, shown  # noqa: E402

STEP_COLUMNS = ["old", "new", "workload", "verdict", "ir_old", "ir_new", "ir_change", "d1_old", "d1_new", "d1_change",
                "why"]


def version_key(release):
    """v2.0.9 before v2.0.10."""
    return tuple(int(p) if p.isdigit() else p for p in release.lstrip("v").replace("-", ".").split("."))


def read(folder):
    """counts by (workload, release), the releases in version order, and the gaps' reasons by (workload, release)."""
    with open(folder / "counts.tsv") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    counts = {(r["workload"], r["ref"]): r for r in rows}
    releases = sorted({r["ref"] for r in rows}, key=version_key)
    why = {}
    if (folder / "gaps.tsv").exists():
        with open(folder / "gaps.tsv") as f:
            why = {(g["workload"], g["release"]): g["why"] for g in csv.DictReader(f, delimiter="\t")}
    return counts, releases, why


def steps(counts, releases):
    out = []
    workloads = sorted({w for w, _ in counts})
    for w in workloads:
        for old_rel, new_rel in zip(releases, releases[1:]):
            old, new = counts.get((w, old_rel)), counts.get((w, new_rel))
            built = lambda r: r is not None and r["bits"] in ("ok", "DIFF")
            if not built(old) and not built(new):
                v, why = "gap", "builds on neither release"
            elif not built(old) and new["bits"] == "ok":
                v, why = "first", "first release it builds on"
            else:
                v, why = judge(old, new)
            counted = v not in ("gap", "first", "missing", "no-baseline") and new["bits"] == "ok" and old["bits"] == "ok"
            row = {"old": old_rel, "new": new_rel, "workload": w, "verdict": v, "why": why}
            for side, r in (("old", old), ("new", new)):
                row[f"ir_{side}"] = r["ir"] if r and r["ir"].isdigit() else "-"
                row[f"d1_{side}"] = r["d1_misses"] if r and r["d1_misses"].isdigit() else "-"
            row["ir_change"] = f"{change(int(old['ir']), int(new['ir'])):.6f}" if counted else "-"
            row["d1_change"] = f"{change(int(old['d1_misses']), int(new['d1_misses'])):.6f}" if counted else "-"
            out.append(row)
    return out


def coverage(counts, releases, why):
    out = []
    for w in sorted({w for w, _ in counts}):
        row = {"workload": w}
        for rel in releases:
            r = counts.get((w, rel))
            if r is None:
                row[rel] = "missing"
            elif r["bits"] == "ok":
                row[rel] = "ok"
            else:
                row[rel] = f"{r['bits']}: {why.get((w, rel), '')}".rstrip(": ")
        out.append(row)
    return out


def overall(counts, releases):
    """Per workload: its first and last counted release and the change in instructions between them."""
    out = []
    for w in sorted({w for w, _ in counts}):
        ok = [rel for rel in releases if counts.get((w, rel), {}).get("bits") == "ok"]
        if len(ok) < 2:
            continue
        a, b = int(counts[(w, ok[0])]["ir"]), int(counts[(w, ok[-1])]["ir"])
        out.append({"workload": w, "first": ok[0], "last": ok[-1], "ir_first": a, "ir_last": b,
                    "change": change(a, b)})
    return out


def per_release(rows, releases):
    """One line a release after the first: the verdicts' counts and the biggest moves in instructions."""
    lines = []
    for rel in releases[1:]:
        rs = [r for r in rows if r["new"] == rel]
        n = lambda *vs: sum(r["verdict"] in vs for r in rs)
        moved = sorted((r for r in rs if r["ir_change"] != "-" and r["verdict"] in ("improvement", "regression", "mixed")),
                       key=lambda r: -abs(float(r["ir_change"])))
        big = ", ".join(f"{r['workload']} {shown(float(r['ir_change']))}" for r in moved[:3])
        lines.append({"release": rel, "faster": n("improvement"), "slower": n("regression"), "mixed": n("mixed"),
                      "same": n("same"), "first": n("first"), "gap": n("gap"), "bits": n("bits"),
                      "biggest": big or "-"})
    return lines


def write_tsv(path, columns, rows):
    with open(path, "w", newline="") as f:
        out = csv.DictWriter(f, columns, delimiter="\t", lineterminator="\n")
        out.writeheader()
        out.writerows(rows)


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    folder = Path(sys.argv[1])
    try:
        counts, releases, why = read(folder)
    except (OSError, KeyError) as e:
        print(f"history_report.py: {e}", file=sys.stderr)
        return 2
    rows = steps(counts, releases)
    write_tsv(folder / "steps.tsv", STEP_COLUMNS, rows)
    cov = coverage(counts, releases, why)
    write_tsv(folder / "coverage.tsv", ["workload"] + releases, cov)
    table = per_release(rows, releases)
    clang = ", ".join(sorted({r["clang"] for r in counts.values()})) or "?"
    vg = ", ".join(sorted({r["valgrind"] for r in counts.values()})) or "?"
    md = [f"# Bend {releases[0]} to {releases[-1]} on the corpus", "",
          f"Every workload counted under Cachegrind (one thread, the simulated caches of `scripts/count.sh`) with each "
          f"release, a workload's releases all on one machine (clang {clang}, valgrind {vg}). A step is a finding when "
          f"instructions move beyond 0.1% or simulated D1 misses beyond 5%, or the output is not its oracle.", "",
          "| release | faster | slower | mixed | same | first counted | not built | output changed | biggest moves (instructions) |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    for t in table:
        md.append(f"| {t['release']} | {t['faster']} | {t['slower']} | {t['mixed']} | {t['same']} | {t['first']} | "
                  f"{t['gap']} | {t['bits']} | {t['biggest']} |")
    md += ["", f"From each workload's first release to {releases[-1]}, instructions:", "",
           "| workload | from | instructions there | instructions on the last | change |", "|---|---|---:|---:|---:|"]
    for o in sorted(overall(counts, releases), key=lambda o: o["change"]):
        md.append(f"| {o['workload']} | {o['first']} | {o['ir_first']:,} | {o['ir_last']:,} | {shown(o['change'])} |")
    gaps = [(c["workload"], rel, c[rel]) for c in cov for rel in releases if c[rel] != "ok"]
    if gaps:
        md += ["", "Not counted (the workload does not build or run there; recorded, not adapted):", ""]
        for w in sorted({g[0] for g in gaps}):
            rels = [g[1] for g in gaps if g[0] == w]
            # one reason however many releases give it: the C file's line and column moves between releases
            reasons = sorted({re.sub(r"\S+\.c:\d+:\d+: ", "", g[2]) for g in gaps if g[0] == w})
            md.append(f"- {w}: {', '.join(rels)} ({'; '.join(reasons)})")
    (folder / "report.md").write_text("\n".join(md) + "\n")
    for t in table:
        print(f"{t['release']:9} faster {t['faster']:2}  slower {t['slower']:2}  mixed {t['mixed']}  same {t['same']:2}  "
              f"first {t['first']}  gap {t['gap']}  bits {t['bits']}  {t['biggest']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
