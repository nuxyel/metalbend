"""The release watch's verdict: two Bends' Cachegrind counts of every workload (scripts/count.sh's rows, both counted
on one machine), compared workload by workload.

    python3 -I scripts/track_verdict.py <counts.tsv> <old ref> <new ref> <out dir> [--run <url>] [--store <path>]
        [--expect "<workload> ..."]

A workload is a finding when its instructions (Ir) move beyond 0.1% of the old count, its simulated D1 misses beyond
5%, or its output is not its oracle on the new Bend. Cachegrind's counts repeat exactly, so the thresholds are about
what is worth reading, not about noise. Verdicts: regression (a count went up), improvement (down), mixed (one up,
one down), same, bits (the new Bend's output is not the oracle, or no longer builds or runs), no-baseline (the old
Bend could not give a count to compare against), missing (no row for a side, or none at all for a workload of
--expect). Writes verdict.tsv and report.md into the out dir, and issue.md with issue-title.txt when there is
something to open an issue about: a regression, a mixed change or bits. Prints one line per finding and a last line
with the counts; exits 0, or 2 on a bad counts file.
"""
import csv
import sys
from pathlib import Path

IR_LIMIT = 0.001   # a change in instructions beyond 0.1% of the old count
D1_LIMIT = 0.05    # a change in simulated D1 misses beyond 5%
COLUMNS = ["workload", "verdict", "ir_old", "ir_new", "ir_change", "d1_old", "d1_new", "d1_change", "ll_old",
           "ll_new", "bits_old", "bits_new", "why"]
ISSUE = ("regression", "mixed", "bits")


def change(old, new):
    """The relative change from old to new; 0 when both are 0."""
    if old == 0:
        return 0.0 if new == 0 else float("inf")
    return (new - old) / old


def shown(c):
    """A change as people read it: +9.33%, or 2.02x once it is a doubling or a halving."""
    if c == float("inf"):
        return "from 0"
    r = 1 + c
    if r >= 2 or r <= 0.5:
        return f"{r:.2f}x"
    return f"{100 * c:+.2f}%"


def judge(old, new):
    """The verdict on one workload from its two rows (dicts of count.sh's columns, or None), and why."""
    if new is None or old is None:
        if new is None and old is None:
            return "missing", "no count for either Bend"
        return "missing", "no count for the " + ("new" if new is None else "old") + " Bend"
    if new["bits"] != "ok":
        if new["bits"] == "DIFF":
            return "bits", f"the output's hash is {new['hash']}, not its oracle"
        return "bits", f"{new['bits']} on the new Bend"
    if old["bits"] != "ok":
        return "no-baseline", f"{old['bits']} on the old Bend"
    ir = change(int(old["ir"]), int(new["ir"]))
    d1 = change(int(old["d1_misses"]), int(new["d1_misses"]))
    up = [f"instructions {shown(ir)}"] if ir > IR_LIMIT else []
    up += [f"D1 misses {shown(d1)}"] if d1 > D1_LIMIT else []
    down = [f"instructions {shown(ir)}"] if ir < -IR_LIMIT else []
    down += [f"D1 misses {shown(d1)}"] if d1 < -D1_LIMIT else []
    if up and down:
        return "mixed", ", ".join(up + down)
    if up:
        return "regression", ", ".join(up)
    if down:
        return "improvement", ", ".join(down)
    return "same", ""


def read_counts(path, old_ref, new_ref):
    """The rows of a counts file by workload and side; a side is the row's ref."""
    with open(path) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    sides = {}
    for r in rows:
        side = "old" if r["ref"] == old_ref else "new" if r["ref"] == new_ref else None
        if side is None:
            raise ValueError(f"a row for {r['workload']} names ref {r['ref']}, neither {old_ref} nor {new_ref}")
        sides.setdefault(r["workload"], {})[side] = r
    return sides


def verdicts(sides):
    out = []
    for w in sorted(sides):
        old, new = sides[w].get("old"), sides[w].get("new")
        v, why = judge(old, new)
        row = {"workload": w, "verdict": v, "why": why}
        for side, r in (("old", old), ("new", new)):
            for col, key in (("ir", "ir"), ("d1", "d1_misses"), ("ll", "ll_misses"), ("bits", "bits")):
                row[f"{col}_{side}"] = r[key] if r else "-"
        counted = old and new and old["bits"] == "ok" and new["bits"] == "ok"
        row["ir_change"] = f"{change(int(old['ir']), int(new['ir'])):.6f}" if counted else "-"
        row["d1_change"] = f"{change(int(old['d1_misses']), int(new['d1_misses'])):.6f}" if counted else "-"
        out.append(row)
    return out


def machine(sides):
    """clang and valgrind as the rows name them (one machine, so one of each)."""
    rows = [r for s in sides.values() for r in s.values()]
    clang = sorted({r["clang"] for r in rows})
    vg = sorted({r["valgrind"] for r in rows})
    return ", ".join(clang) or "?", ", ".join(vg) or "?"


def commit_of(sides, side):
    cs = sorted({s[side]["commit"] for s in sides.values() if side in s})
    return cs[0] if len(cs) == 1 else ", ".join(cs) or "?"


def table(rows):
    lines = ["| workload | instructions | D1 misses | output | verdict |", "|---|---:|---:|---|---|"]
    for r in rows:
        ir = shown(float(r["ir_change"])) if r["ir_change"] != "-" else "-"
        d1 = shown(float(r["d1_change"])) if r["d1_change"] != "-" else "-"
        bits = "its oracle" if r["bits_new"] == "ok" else r["bits_new"]
        lines.append(f"| {r['workload']} | {ir} | {d1} | {bits} | {r['verdict']} |")
    return lines


def write(out, rows, old_ref, new_ref, sides, run=None, store=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "verdict.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, COLUMNS, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    clang, vg = machine(sides)
    head = (f"Bend {new_ref} ({commit_of(sides, 'new')[:12]}) against {old_ref} ({commit_of(sides, 'old')[:12]}), "
            f"every workload counted under Cachegrind on one thread with both versions on one machine (clang {clang}, "
            f"valgrind {vg}). A finding is a change in instructions beyond {100 * IR_LIMIT:g}% or in simulated D1 "
            f"misses beyond {100 * D1_LIMIT:g}%, or an output that is not its oracle.")
    found = [r for r in rows if r["verdict"] not in ("same", "no-baseline")]
    report = [f"# Release watch: {new_ref} against {old_ref}", "", head, ""] + table(rows)
    report += ["", f"{len(found)} of {len(rows)} workloads moved or changed their output."]
    for r in rows:
        if r["why"]:
            report.append(f"- {r['workload']}: {r['verdict']}, {r['why']}")
    links = []
    if store:
        links.append(f"The counts: `{store}` on the `data` branch.")
    if run:
        links.append(f"The run: {run}.")
    report += [""] + links if links else []
    (out / "report.md").write_text("\n".join(report) + "\n")
    for f in ("issue.md", "issue-title.txt"):
        (out / f).unlink(missing_ok=True)
    flagged = [r for r in rows if r["verdict"] in ISSUE]
    if not flagged:
        return found, flagged
    kinds = sorted({r["verdict"] for r in flagged}, key=ISSUE.index)
    title = f"Bend {new_ref}: {', '.join(kinds)} in {len(flagged)} workload{'s' if len(flagged) > 1 else ''} " \
            f"against {old_ref}"
    issue = [head, ""] + table(flagged) + [""]
    for r in flagged:
        issue.append(f"- {r['workload']}: {r['why']}")
    better = [r for r in rows if r["verdict"] == "improvement"]
    if better:
        issue += ["", "Improvements in the same run: " +
                  "; ".join(f"{r['workload']} ({r['why']})" for r in better) + "."]
    issue += ["", "To count them again, from a clone of this repository (bun, clang and valgrind on PATH):", "",
              "```sh", "make data"]
    for r in flagged:
        issue += [f"scripts/count.sh {old_ref} {r['workload']}", f"scripts/count.sh {new_ref} {r['workload']}"]
    issue += ["```"]
    issue += [""] + links if links else []
    (out / "issue.md").write_text("\n".join(issue) + "\n")
    (out / "issue-title.txt").write_text(title + "\n")
    return found, flagged


def main(argv):
    args, opts = [], {}
    it = iter(argv)
    for a in it:
        if a in ("--run", "--store", "--expect"):
            opts[a[2:]] = next(it, None)
        else:
            args.append(a)
    if len(args) != 4:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    counts, old_ref, new_ref, out = args
    try:
        sides = read_counts(counts, old_ref, new_ref)
    except (OSError, KeyError, ValueError) as e:
        print(f"track_verdict: {e}", file=sys.stderr)
        return 2
    for w in (opts.get("expect") or "").split():
        sides.setdefault(w, {})
    rows = verdicts(sides)
    found, flagged = write(out, rows, old_ref, new_ref, sides, opts.get("run"), opts.get("store"))
    for r in found:
        print(f"{r['workload']}: {r['verdict']}, {r['why']}")
    print(f"{len(found)} of {len(rows)} workloads moved or changed their output; "
          f"{len(flagged)} for an issue{'' if flagged else ' (none written)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
