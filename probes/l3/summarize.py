"""Summarizes a run.sh table: per binary and condition, the median and spread ((max - min) / median) of user-mode
instructions, cycles and L3 misses over the rounds; the busy / idle change of each median; and the Bend / C cycle
ratios, taken within each round and condition and then summarized the same way.
    python3 -I probes/l3/summarize.py probes/l3/results/<file>.tsv
Pairs: gemm-fork and gemm-tile8 against their own C targets, and gemm-fork against gemm-tile8's C (the old pairing)."""
import csv
import statistics
import sys
from collections import defaultdict

rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
hashes = {r["hash"] for r in rows}
by = defaultdict(lambda: defaultdict(list))  # (cond, binary) -> column -> values
cell = {}                                    # (round, cond, binary) -> cycles
for r in rows:
    k = (r["cond"], r["binary"])
    for c in ("instructions_u", "cycles_u", "l3_miss_u", "seconds"):
        by[k][c].append(float(r[c]))
    cell[(r["round"], r["cond"], r["binary"])] = float(r["cycles_u"])
rounds = sorted({r["round"] for r in rows}, key=int)
bins = sorted({r["binary"] for r in rows})
conds = ["idle", "busy"]


def med_spread(v):
    m = statistics.median(v)
    return m, (max(v) - min(v)) / m if m else 0.0


print(f"{len(rows)} runs, {len(rounds)} rounds, hashes: {', '.join(sorted(hashes))}")
gbs = sorted({float(r["stream_gbs"]) for r in rows if r["stream_gbs"]})
if gbs:
    print(f"antagonists' summed rate: {gbs[0]:.1f}-{gbs[-1]:.1f} GB/s")
la = [float(r["loadavg"]) for r in rows if r["cond"] == "idle"]
print(f"load average before the idle runs: {min(la):.2f}-{max(la):.2f}\n")
print("| binary | cond | Minstr | Mcycles (spread) | L3 misses, M (spread) | cycles busy / idle |")
print("|---|---|---:|---:|---:|---:|")
for b in bins:
    for c in conds:
        d = by[(c, b)]
        if not d:
            continue
        i, _ = med_spread(d["instructions_u"])
        y, ys = med_spread(d["cycles_u"])
        l, ls = med_spread(d["l3_miss_u"])
        ch = ""
        if c == "busy" and by[("idle", b)]:
            ch = f"{y / statistics.median(by[('idle', b)]['cycles_u']):.3f}x"
        print(f"| {b} | {c} | {i / 1e6:.1f} | {y / 1e6:.1f} ({ys:.1%}) | {l / 1e6:.3f} ({ls:.0%}) | {ch} |")

pairs = []
for b in bins:
    if b.endswith("-c"):
        continue
    w = b.rsplit("-", 1)[0]
    pairs.append((b, f"{w}-c"))
    if w == "gemm-fork":
        pairs.append((b, "gemm-tile8-c"))
print("\n| Bend / C, cycles | idle: median (range) | busy: median (range) | busy / idle |")
print("|---|---:|---:|---:|")
for b, c in pairs:
    out, meds = [], []
    for cond in conds:
        v = [cell[(r, cond, b)] / cell[(r, cond, c)] for r in rounds
             if (r, cond, b) in cell and (r, cond, c) in cell]
        m = statistics.median(v)
        meds.append(m)
        out.append(f"{m:.3f} ({min(v):.3f}-{max(v):.3f})")
    print(f"| {b} / {c} | {out[0]} | {out[1]} | {meds[1] / meds[0]:.3f} |")
