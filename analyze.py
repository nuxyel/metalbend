"""Reads a run's runs.tsv and writes summary.md next to it.

    python3 -I analyze.py results/<date>

Per workload and Bend version: the median of user-mode instructions and cycles and of seconds over the rounds, and their spread
(max - min over the median). Against the newest version, each older one's change, marked as beyond noise when it is
larger than three times the larger spread of the two, with floors of 0.1% (instructions) and 1% (cycles), and only
with at least 3 rounds on both sides. Outputs: every run of a workload must print the same bytes
(the same hash) at every version; a differing hash is listed, never averaged away. The C targets (bend "c") are
compared with the newest version: the ratio of their medians, and whether they print the same bytes. Runs on more
threads (column `threads`) get their own table: wall-time speedup over one thread, and whether every thread count
prints the same bytes.
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def spread(xs):
    m = statistics.median(xs)
    return (max(xs) - min(xs)) / m if m else 0.0


def main(out):
    out = Path(out)
    allruns = list(csv.DictReader(open(out / "runs.tsv"), delimiter="\t"))
    for r in allruns:
        r["threads"] = int(r.get("threads") or 1)
    runs = [r for r in allruns if r["threads"] == 1]
    cell = defaultdict(lambda: {"ins": [], "cyc": [], "sec": [], "hash": set(), "bad": 0})
    for r in runs:
        c = cell[(r["workload"], r["bend"] if r["bend"] == "c" else int(r["bend"]))]
        if r["status"] != "ok" or not r["instructions"].isdigit():
            c["bad"] += 1
            continue
        c["ins"].append(int(r["instructions"]))
        c["cyc"].append(int(r["cycles"]))
        c["sec"].append(float(r["seconds"]))
        c["hash"].add(r["hash"])
    native = {w: cell.pop((w, "c")) for w, v in list(cell) if v == "c"}
    workloads = sorted({w for w, _ in cell})
    versions = sorted({v for _, v in cell})
    base = versions[-1]
    lines = [f"# {out.name}", "", f"Rounds per pair: {max(len(c['ins']) + c['bad'] for c in cell.values())}. "
             f"Changes are against Bend 2.0.{base}; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).", ""]
    lines += ["| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|---|"]
    findings = []
    for w in workloads:
        bc = cell.get((w, base))
        bhash = next(iter(bc["hash"])) if bc and len(bc["hash"]) == 1 else None
        for v in versions:
            c = cell.get((w, v))
            if not c or not c["ins"]:
                lines.append(f"| {w} | 2.0.{v} | - | - | - | - | - | - | - | {'no build' if not c else 'failed'} |")
                continue
            mi, mc, ms = (statistics.median(c[k]) for k in ("ins", "cyc", "sec"))
            si, sc = spread(c["ins"]), spread(c["cyc"])
            di = dc = ""
            if v != base and bc and bc["ins"]:
                bi, bcy = statistics.median(bc["ins"]), statistics.median(bc["cyc"])
                enough = min(len(c["ins"]), len(bc["ins"])) >= 3
                for name, d, noise in (("instructions", mi / bi - 1, max(si, spread(bc["ins"]), 0.001)),
                                       ("cycles", mc / bcy - 1, max(sc, spread(bc["cyc"]), 0.01))):
                    txt = f"{d * 100:+.2f}%"
                    if enough and abs(d) > 3 * noise:
                        txt = f"**{txt}**"
                        findings.append(f"- {w}: 2.0.{v} {name} {d * 100:+.2f}% against 2.0.{base} (noise {noise * 100:.2f}%)")
                    if name == "instructions":
                        di = txt
                    else:
                        dc = txt
            hs = ", ".join(sorted(c["hash"]))
            if len(c["hash"]) > 1:
                findings.append(f"- {w}: 2.0.{v} printed {len(c['hash'])} different outputs across its rounds")
            elif bhash and hs != bhash:
                findings.append(f"- {w}: 2.0.{v}'s output differs from 2.0.{base}'s ({hs} against {bhash})")
            lines.append(f"| {w} | 2.0.{v} | {mi / 1e6:.1f} | {si * 100:.2f}% | {mc / 1e6:.1f} | {sc * 100:.2f}% | "
                         f"{ms:.3f} | {di} | {dc} | {hs}{' (+' + str(c['bad']) + ' failed)' if c['bad'] else ''} |")
    if native:
        lines += ["", f"## Against the C targets (Bend 2.0.{base} / C, medians)", "",
                  "| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |",
                  "|---|---:|---:|---:|---:|---:|---:|---|"]
        for w, c in sorted(native.items()):
            bc = cell.get((w, base))
            if not c["ins"] or not bc or not bc["ins"]:
                continue
            mi, mc, ms = (statistics.median(c[k]) for k in ("ins", "cyc", "sec"))
            same = c["hash"] == bc["hash"] and len(c["hash"]) == 1
            if not same:
                findings.append(f"- {w}: the C target's output differs from Bend 2.0.{base}'s")
            lines.append(f"| {w} | {mi / 1e6:.1f} | {mc / 1e6:.1f} | {ms:.3f} | "
                         f"{statistics.median(bc['ins']) / mi:.2f}x | {statistics.median(bc['cyc']) / mc:.2f}x | "
                         f"{statistics.median(bc['sec']) / ms:.2f}x | {'yes' if same else '**no**'} |")
    multi = sorted({r["threads"] for r in allruns} - {1})
    if multi:
        sec = defaultdict(list)
        hashes = defaultdict(set)
        for r in allruns:
            if r["bend"] == "c" or r["status"] != "ok":
                continue
            sec[(r["workload"], int(r["bend"]), r["threads"])].append(float(r["seconds"]))
            hashes[(r["workload"], int(r["bend"]))].add(r["hash"])
        head = " | ".join(f"{t} threads s | speedup" for t in multi)
        lines += ["", "## Threads (wall time, medians; the output must be the same at every thread count)", "",
                  f"| workload | bend | 1 thread s | {head} | same output |",
                  "|---|---|---:|" + "---:|---:|" * len(multi) + "---|"]
        for w in workloads:
            for v in versions:
                one = sec.get((w, v, 1))
                if not one:
                    continue
                m1 = statistics.median(one)
                cols = []
                for t in multi:
                    xs = sec.get((w, v, t))
                    cols += [f"{statistics.median(xs):.3f}", f"{m1 / statistics.median(xs):.2f}x"] if xs else ["-", "-"]
                same = len(hashes[(w, v)]) == 1
                if not same:
                    findings.append(f"- {w}: 2.0.{v} prints different outputs across thread counts")
                lines.append(f"| {w} | 2.0.{v} | {m1:.3f} | " + " | ".join(cols) + f" | {'yes' if same else '**no**'} |")
    lines += ["", "## Beyond noise or differing outputs", ""] + (findings or ["None."])
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
