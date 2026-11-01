"""Compares the hashes of a run (run.sh's runs.tsv) with oracles.tsv, case by case.

    python3 -I scripts/oracle_diff.py results/<date>-2.0.40            # against oracles.tsv
    python3 -I scripts/oracle_diff.py <run> <oracles.tsv>

A case is a workload on one Bend version and thread count, or its C target. Every run of a case must have exit
status ok and print the workload's oracle; a case that fails, prints another hash, or has no oracle line is listed.
Every workload of oracles.tsv must have run on every version of the run (a missing build is listed too). With a
gpu.tsv (GPU=1), each GPU target is a case too, against its line <name>:gpu; a :gpu line is only required then. Prints one
line per problem and a last line with the count; exits 1 if there is any problem, 0 otherwise. release.sh prints it
at the end, so a new release says at once whether any output moved from the recorded oracle.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def full(v):
    """A version's full name: 2.0.x versions are named by their last number in a run, later ones in full."""
    return v if "." in v else f"2.0.{v}"


def label(w, v, t):
    if v == "c":
        return f"{w}, C target"
    if t == "gpu":
        return f"{w}, GPU target, Bend {full(v)}"
    return f"{w}, Bend {full(v)}, {t} thread{'' if t == '1' else 's'}"


def compare(out, oracles=ROOT / "oracles.tsv"):
    """The problems as lines, and the number of cases read."""
    with open(oracles) as f:
        want = {r["workload"]: r["hash"] for r in csv.DictReader(f, delimiter="\t") if r["workload"]}
    with open(Path(out) / "runs.tsv") as f:
        runs = list(csv.DictReader(f, delimiter="\t"))
    cases = defaultdict(lambda: {"hash": set(), "bad": []})
    for r in runs:
        c = cases[(r["workload"], r["bend"], r.get("threads") or "1")]
        if r["status"] != "ok":
            c["bad"].append(r["status"])
        else:
            c["hash"].add(r["hash"])
    gpu = Path(out) / "gpu.tsv"
    if gpu.exists():
        with open(gpu) as f:
            for r in csv.DictReader(f, delimiter="\t"):
                c = cases[(r["workload"] + ":gpu", r["bend"], "gpu")]
                if r["status"] != "ok":
                    c["bad"].append(r["status"])
                else:
                    c["hash"].add(r["hash"])
    problems = []
    for (w, v, t), c in sorted(cases.items()):
        name = label(w.removesuffix(":gpu"), v, t)
        if w not in want:
            problems.append(f"NO ORACLE {name}: no line for {w} in oracles.tsv")
            continue
        if c["bad"]:
            problems.append(f"FAILED    {name}: {len(c['bad'])} run(s) ended with {', '.join(sorted(set(c['bad'])))}")
        other = sorted(c["hash"] - {want[w]})
        if other:
            problems.append(f"DIFFERS   {name}: {', '.join(other)}, oracle {want[w]}")
    if not cases:
        problems.append("NO RUNS   runs.tsv has no runs (ROUNDS=0, or nothing built)")
    versions = sorted({v for _, v, _ in cases if v != "c"})
    for w in sorted(want):
        if w.endswith(":gpu") and not gpu.exists():
            continue
        for v in versions:
            if not any(cw == w and cv == v for cw, cv, _ in cases):
                problems.append(f"MISSING   {w}, Bend {full(v)}: no run (did it build?)")
    return problems, len(cases)


def main(argv):
    problems, n = compare(*argv[1:3])
    if problems:
        print("\n".join(problems))
        print(f"oracles: {len(problems)} problem(s) in {n} cases against oracles.tsv")
        return 1
    print(f"oracles: {n} cases, every hash is its oracle")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
