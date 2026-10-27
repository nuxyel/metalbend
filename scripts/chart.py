"""Draws a results chart from the raw runs in results/ (no numbers are typed in here).

    python3 -I scripts/chart.py                                  # docs/results-2.0.39.svg, from the runs of record
    python3 -I scripts/chart.py 40 results/<date>-2.0.40         # docs/results-2.0.40.svg, from release.sh's run

Two panels, both on one Bend version:
- top: Bend / C in user-mode cycles on one thread, for the six workloads with a C target (median over the rounds of
  the run of record, the same numbers as README.md);
- bottom: the wall-time speedup on 16 threads over one thread, for all eleven workloads.
Plain SVG, standard library only, so it runs from a fresh clone.
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
# with no arguments, 2.0.39 and the run of record for each number, as README.md and NOTES.md cite them
VERSION = "39"
C_RUNS = {"gemm-tile8": "2026-10-25-d", "matvec-bands": "2026-10-25-d", "softmax-ce": "2026-10-25-d",
          "adamw": "2026-10-25-f", "mnist-step": "2026-10-25-f", "read-native": "2026-10-25-f"}
THREAD_RUN = "2026-10-25-f"
ROUNDS = {}  # rounds per run used

LABELS = {
    "gemm-tile8": "matrix product",
    "gemm-fork": "matrix product, parallel blocks",
    "matvec-bands": "matrix-vector product",
    "softmax-ce": "softmax and cross-entropy",
    "mnist-step": "MNIST training step",
    "block-step": "transformer block, forward + backward",
    "attention-step": "attention, forward + backward",
    "rmsnorm-step": "RMSNorm",
    "adamw": "AdamW optimizer step",
    "read-native": "16 MB file read, built-in",
    "read-binary": "16 MB file read, bend-ml-binary-read",
}
NOTES = {
    "gemm-tile8": "a sequential loop by design",
    "mnist-step": "its loops run one after another",
    "softmax-ce": "its loops run one after another",
    "adamw": "its loops run one after another",
    "rmsnorm-step": "its loops run one after another",
    "read-native": "slower: starting the workers costs more",
    "read-binary": "slower: starting the workers costs more",
}


def runs(name):
    return list(csv.DictReader(open(ROOT / "results" / name / "runs.tsv"), delimiter="\t"))


def ok(r):
    return r["status"] == "ok" and r["instructions"].isdigit()


def c_ratios():
    out = {}
    cache = {}
    for w, run in C_RUNS.items():
        rs = cache.setdefault(run, runs(run))
        ROUNDS[run] = max(int(r["round"]) for r in rs)
        cyc = defaultdict(list)
        hashes = defaultdict(set)
        for r in rs:
            if r["workload"] == w and ok(r) and int(r.get("threads") or 1) == 1 and r["bend"] in (VERSION, "c"):
                cyc[r["bend"]].append(int(r["cycles"]))
                hashes[r["bend"]].add(r["hash"])
        assert hashes[VERSION] == hashes["c"] and len(hashes["c"]) == 1, f"{w}: C and Bend outputs differ"
        out[w] = statistics.median(cyc[VERSION]) / statistics.median(cyc["c"])
    return out


def speedups():
    sec = defaultdict(list)
    hashes = defaultdict(set)
    for r in runs(THREAD_RUN):
        ROUNDS[THREAD_RUN] = max(ROUNDS.get(THREAD_RUN, 0), int(r["round"]))
        if r["bend"] == VERSION and r["status"] == "ok":
            sec[(r["workload"], int(r["threads"]))].append(float(r["seconds"]))
            hashes[r["workload"]].add(r["hash"])
    out = {}
    for w in {w for w, _ in sec}:
        assert len(hashes[w]) == 1, f"{w}: outputs differ across thread counts"
        out[w] = statistics.median(sec[(w, 1)]) / statistics.median(sec[(w, 16)])
    return out


def fmt(x):
    return f"{x:.0f}x" if x >= 10 else f"{x:.2f}x"


W = 820
LEFT = 290          # label column
RIGHT = 120         # room for values and notes past the axis end
ROW = 36
BAR = 18


def text(x, y, s, cls, anchor="start"):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>'


def panel(y0, title, subtitle, rows, xmax, ticks, ref_label, color_of, note_of, cut=None):
    """Horizontal bars from 0; rows is [(workload, value)]. Returns (svg parts, height)."""
    parts = [text(24, y0 + 22, title, "title"), text(24, y0 + 44, subtitle, "sub")]
    top = y0 + 70
    plot_w = W - LEFT - RIGHT - 24
    sx = lambda v: LEFT + plot_w * min(v, xmax) / xmax
    h = ROW * len(rows)
    for t in ticks:
        x = sx(t)
        parts.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{top + h}" class="grid"/>')
        parts.append(text(x, top + h + 16, f"{t:g}x", "tick", "middle"))
    x1 = sx(1)
    parts.append(f'<line x1="{x1:.1f}" y1="{top - 10}" x2="{x1:.1f}" y2="{top + h}" class="ref"/>')
    parts.append(text(x1 + 4, top - 12, ref_label, "reflabel"))
    for i, (w, v) in enumerate(rows):
        cy = top + i * ROW + ROW / 2
        parts.append(text(LEFT - 12, cy - 2, LABELS[w], "label", "end"))
        parts.append(text(LEFT - 12, cy + 12, w, "name", "end"))
        x = sx(v)
        y = cy - BAR / 2
        parts.append(f'<rect x="{LEFT}" y="{y:.1f}" width="{x - LEFT:.1f}" height="{BAR}" rx="3" class="{color_of(v)}"/>')
        label = fmt(v)
        if cut and v > xmax:
            # the bar is cut at the axis end: two slanted gaps mark the break
            for dx in (-22, -14):
                parts.append(f'<line x1="{x + dx - 3:.1f}" y1="{y + BAR + 2:.1f}" x2="{x + dx + 3:.1f}" y2="{y - 2:.1f}" class="cut"/>')
            label += cut
        note = note_of(w)
        parts.append(text(x + 6, cy + 4, label, "value"))
        if note:
            parts.append(text(x + 6 + 7.5 * len(label) + 8, cy + 4, note, "note"))
    return parts, 70 + h + 30


def main():
    global VERSION, C_RUNS, THREAD_RUN
    if len(sys.argv) > 1:
        VERSION, run = sys.argv[1], Path(sys.argv[2]).name
        THREAD_RUN = run
        C_RUNS = {w: run for w in sorted({r["workload"] for r in runs(run) if r["bend"] == "c"})}
    out_path = ROOT / "docs" / f"results-2.0.{VERSION}.svg"
    ratios = c_ratios()
    speed = speedups()
    parts = []
    y = 16
    p, h = panel(y, f"How far Bend 2.0.{VERSION} is from handwritten C",
                 "CPU cycles of Bend's program per cycle of a C version that prints the same bits; one thread. "
                 "Lower is better.",
                 sorted(ratios.items(), key=lambda kv: kv[1]), 6, range(0, 7), "1x = as fast as C",
                 lambda v: "bar", lambda w: "", cut=", bar cut to fit")
    parts += p
    y += h + 20
    p, h = panel(y, "What 16 threads buy over one",
                 "Wall-time speedup of the same program on 16 threads; the output is the same at both. "
                 "Higher is better.",
                 sorted(speed.items(), key=lambda kv: -kv[1]), 5, range(0, 6), "1x = no gain",
                 lambda v: "bar" if v >= 1.1 else "flat", lambda w: NOTES.get(w, "") if speed[w] < 1.1 else "")
    parts += p
    y += h + 6
    parts.append(text(24, y + 8, "Core Ultra 7 155H. One thread: pinned to a P-core, user-mode cycles from perf stat. "
                      f"Medians over {'-'.join(str(n) for n in sorted(set(ROUNDS.values())))} round{'s' if max(ROUNDS.values()) > 1 else ''}.", "foot"))
    parts.append(text(24, y + 24, "Source: runs.tsv in " + " and ".join(
        f"results/{r}" for r in sorted(set(C_RUNS.values()) | {THREAD_RUN})) + ".", "foot"))
    height = y + 40
    style = """
  svg { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
  .bg { fill: #fcfcfb; }
  .title { font-size: 19px; font-weight: 600; fill: #0b0b0b; }
  .sub { font-size: 13px; fill: #52514e; }
  .label { font-size: 13.5px; fill: #0b0b0b; }
  .name { font-size: 11px; fill: #6f6e69; font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace; }
  .value { font-size: 13px; font-weight: 600; fill: #0b0b0b; paint-order: stroke; stroke: #fcfcfb; stroke-width: 4px; }
  .note { font-size: 12px; fill: #6f6e69; paint-order: stroke; stroke: #fcfcfb; stroke-width: 4px; }
  .tick { font-size: 11px; fill: #6f6e69; }
  .reflabel { font-size: 11.5px; fill: #52514e; }
  .foot { font-size: 11px; fill: #6f6e69; }
  .grid { stroke: #e6e5e0; stroke-width: 1; }
  .ref { stroke: #52514e; stroke-width: 1.5; stroke-dasharray: 4 3; }
  .bar { fill: #2a78d6; }
  .flat { fill: #b4b2a9; }
  .cut { stroke: #fcfcfb; stroke-width: 3; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1a1a19; }
    .title, .label, .value { fill: #f0efec; }
    .sub, .reflabel { fill: #c3c2b7; }
    .name, .note, .tick, .foot { fill: #9d9c94; }
    .grid { stroke: #33332f; }
    .ref { stroke: #c3c2b7; }
    .bar { fill: #3987e5; }
    .flat { fill: #6f6e69; }
    .cut, .value, .note { stroke: #1a1a19; }
  }"""
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height:.0f}" viewBox="0 0 {W} {height:.0f}" '
           f'role="img" aria-labelledby="t">',
           f'<title id="t">Bend 2.0.{VERSION} against handwritten C, and its speedups on 16 threads</title>',
           f"<style>{style}\n</style>", f'<rect class="bg" width="{W}" height="{height:.0f}"/>'] + parts + ["</svg>"]
    out_path.write_text("\n".join(svg) + "\n")
    print(f"{out_path.relative_to(ROOT)}")
    for w, v in sorted(ratios.items(), key=lambda kv: kv[1]):
        print(f"  C ratio  {w:15} {fmt(v)}")
    for w, v in sorted(speed.items(), key=lambda kv: -kv[1]):
        print(f"  16 thr   {w:15} {fmt(v)}")


if __name__ == "__main__":
    main()
