"""Draws the history chart from a history folder (scripts/history.sh's counts, gathered by history.yml on the data
branch; no numbers are typed in here).

    python3 -I scripts/history_chart.py <folder>              # docs/history.svg
    python3 -I scripts/history_chart.py <folder> <out.svg>    # elsewhere

One small chart a workload: its instructions under Cachegrind on every release of the folder, relative to the first
release it builds on (1 = as many as there), one shared scale for all, so the lines compare. A triangle marks a release
where the count moved beyond 0.1% (down: fewer instructions, up: more), a gray band the releases where the workload
does not build. Workloads ordered by their change from first to last. Plain SVG, standard library only.
"""
import csv
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart import LABELS  # noqa: E402
from history_report import version_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 0.001     # the release watch's threshold on instructions
FLOOR = 0.6       # the scale's lowest bound: a line below it is cut there, its label still its value

W = 820
COLS = 3
PAD = 24
GAP_X = 22
CELL_H = 132
PLOT_TOP = 40     # inside a cell: the two lines of its label above the plot
PLOT_H = 64


def text(x, y, s, cls, anchor="start"):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{escape(s)}</text>'


def pct(r):
    c = 100 * (r - 1)
    return "0%" if abs(c) < 0.05 else f"{c:+.1f}%".replace("-", "−")


def read(folder):
    with open(folder / "counts.tsv") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    releases = sorted({r["ref"] for r in rows}, key=version_key)
    series = {}
    for r in rows:
        series.setdefault(r["workload"], {})[r["ref"]] = int(r["ir"]) if r["bits"] == "ok" else None
    clang = sorted({r["clang"] for r in rows})
    return releases, series, clang


def nice(lo, hi):
    """Round bounds for the shared scale around 1, in steps of 10% (5% when everything moves under 15%)."""
    step = 0.05 if max(1 - lo, hi - 1) < 0.15 else 0.10
    lo_b = 1 - step * max(1, math.ceil((1 - lo) / step - 1e-9))
    hi_b = 1 + step * max(1, math.ceil((hi - 1) / step - 1e-9))
    return round(lo_b, 4), round(hi_b, 4), step


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    folder = Path(sys.argv[1]).resolve()
    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / "docs" / "history.svg"
    releases, series, clang = read(folder)
    rel = {}
    total = {}
    for w, s in series.items():
        counted = [r for r in releases if s.get(r)]
        if not counted:
            continue
        base = s[counted[0]]
        rel[w] = {r: (s[r] / base if s.get(r) else None) for r in releases}
        total[w] = rel[w][counted[-1]]
    order = sorted(rel, key=lambda w: (total[w], w))
    lo, hi, step = nice(min(v for w in rel for v in rel[w].values() if v), max(v for w in rel for v in rel[w].values() if v))
    cut = lo < FLOOR
    lo = max(lo, FLOOR)
    short = lambda r: r.rsplit(".", 1)[-1]
    cell_w = (W - 2 * PAD - (COLS - 1) * GAP_X) / COLS
    plot_l, plot_r = 34, 46          # room for the scale's labels on the left, the last value on the right
    parts = [text(PAD, 38, f"Bend {releases[0].lstrip('v')} to {releases[-1].lstrip('v')} on {len(order)} real ML workloads",
                  "title"),
             text(PAD, 60, "Instructions on every release against the first release each workload builds on (0% = as "
                  "many). Lower is faster.", "sub"),
             f'<polygon points="{PAD},{77} {PAD + 9},{77} {PAD + 4.5},{85}" class="down"/>',
             text(PAD + 14, 85, "fewer instructions than the release before (beyond 0.1%)", "key"),
             f'<polygon points="{PAD + 330},{85} {PAD + 339},{85} {PAD + 334.5},{77}" class="up"/>',
             text(PAD + 344, 85, "more", "key"),
             f'<rect x="{PAD + 392}" y="74" width="16" height="12" class="gapband"/>',
             text(PAD + 414, 85, "does not build on that release", "key")]
    y0 = 104
    for i, w in enumerate(order):
        cx = PAD + (i % COLS) * (cell_w + GAP_X)
        cy = y0 + (i // COLS) * CELL_H
        x0, x1 = cx + plot_l, cx + cell_w - plot_r
        top, bot = cy + PLOT_TOP, cy + PLOT_TOP + PLOT_H
        sx = lambda k: x0 + (x1 - x0) * k / (len(releases) - 1)
        sy = lambda v: bot - (bot - top) * (max(v, lo) - lo) / (hi - lo)
        parts.append(text(cx, cy + 14, LABELS.get(w, w), "label"))
        parts.append(text(cx, cy + 28, w, "name"))
        half = (x1 - x0) / (len(releases) - 1) / 2
        k = 0
        while k < len(releases):
            if rel[w][releases[k]] is None:
                # one band over a run of releases it does not build on
                j = k
                while j + 1 < len(releases) and rel[w][releases[j + 1]] is None:
                    j += 1
                a, b = max(x0, sx(k) - half), min(x1, sx(j) + half)
                parts.append(f'<rect x="{a:.1f}" y="{top:.1f}" width="{b - a:.1f}" height="{PLOT_H}" class="gapband"/>')
                k = j
            k += 1
        for g in (lo, 1, hi):
            y = sy(g)
            parts.append(f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" class="{"base" if g == 1 else "grid"}"/>')
            if i % COLS == 0:
                parts.append(text(x0 - 5, y + 3.5, f"{100 * (g - 1):+.0f}%".replace("+0%", "0%").replace("-", "\u2212"), "tick", "end"))
        pts = [(sx(k), sy(rel[w][r])) for k, r in enumerate(releases) if rel[w][r] is not None]
        parts.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" class="line"/>')
        prev = None
        for k, r in enumerate(releases):
            v = rel[w][r]
            if v is None:
                prev = None
                continue
            x, y = sx(k), sy(v)
            if v < lo:
                # below the floor: two slanted strokes across the line mark the cut
                for dy in (-9, -5):
                    parts.append(f'<line x1="{x - 5:.1f}" y1="{y + dy + 2:.1f}" x2="{x + 5:.1f}" y2="{y + dy - 2:.1f}" class="cut"/>')
            if prev is not None and abs(v / prev - 1) > LIMIT:
                if v < prev:
                    parts.append(f'<polygon points="{x - 5:.1f},{y - 4:.1f} {x + 5:.1f},{y - 4:.1f} {x:.1f},{y + 5:.1f}" class="down"/>')
                else:
                    parts.append(f'<polygon points="{x - 5:.1f},{y + 4:.1f} {x + 5:.1f},{y + 4:.1f} {x:.1f},{y - 5:.1f}" class="up"/>')
            else:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" class="dot"/>')
            prev = v
        lx, ly = pts[-1]
        parts.append(text(lx + 7, ly + 4, pct(total[w]), "value"))
        if i // COLS == (len(order) - 1) // COLS or i + COLS >= len(order):
            for k, r in enumerate(releases):
                parts.append(text(sx(k), bot + 15, short(r), "tick", "middle"))
    rows = -(-len(order) // COLS)
    y = y0 + rows * CELL_H + 8
    foot = [f"Releases 2.0.{short(releases[0])}-2.0.{short(releases[-1])} along each axis. Cachegrind's instruction count, "
            f"one thread; each workload's releases counted one after",
            f"another on one GitHub runner (clang {', '.join(clang)}), so a line compares with itself."
            + (f" A line below {100 * (lo - 1):.0f}% is cut there; its label is its value.".replace("-", "\u2212") if cut else "")]
    shown = folder.relative_to(ROOT) if folder.is_relative_to(ROOT) else f"history/{folder.name}"
    foot.append(f"Source: counts.tsv in {shown} on the data branch (scripts/history_chart.py).")
    for k, line in enumerate(foot):
        parts.append(text(PAD, y + 16 * k, line, "foot"))
    height = y + 16 * len(foot) + 12
    style = """
  svg { font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; }
  .bg { fill: #fcfcfb; }
  .title { font-size: 19px; font-weight: 600; fill: #0b0b0b; }
  .sub { font-size: 13px; fill: #52514e; }
  .key { font-size: 12px; fill: #52514e; }
  .label { font-size: 13px; font-weight: 600; fill: #0b0b0b; }
  .name { font-size: 10.5px; fill: #6f6e69; font-family: ui-monospace, 'SFMono-Regular', Menlo, monospace; }
  .value { font-size: 12px; font-weight: 600; fill: #0b0b0b; }
  .tick { font-size: 10px; fill: #6f6e69; }
  .foot { font-size: 11px; fill: #6f6e69; }
  .grid { stroke: #e6e5e0; stroke-width: 1; }
  .base { stroke: #b4b2a9; stroke-width: 1; stroke-dasharray: 3 3; }
  .line { fill: none; stroke: #52514e; stroke-width: 2; stroke-linejoin: round; }
  .dot { fill: #52514e; }
  .down { fill: #2a78d6; stroke: #fcfcfb; stroke-width: 1.5; }
  .up { fill: #e34948; stroke: #fcfcfb; stroke-width: 1.5; }
  .gapband { fill: #ebeae6; }
  .cut { stroke: #52514e; stroke-width: 1.5; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #1a1a19; }
    .title, .label, .value { fill: #f0efec; }
    .sub, .key { fill: #c3c2b7; }
    .name, .tick, .foot { fill: #9d9c94; }
    .grid { stroke: #33332f; }
    .base { stroke: #6f6e69; }
    .line { stroke: #c3c2b7; }
    .dot { fill: #c3c2b7; }
    .down { fill: #3987e5; stroke: #1a1a19; }
    .up { fill: #e66767; stroke: #1a1a19; }
    .gapband { fill: #2a2a28; }
    .cut { stroke: #c3c2b7; }
  }"""
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height:.0f}" viewBox="0 0 {W} {height:.0f}" '
           f'role="img" aria-labelledby="t">',
           f'<title id="t">Instructions of {len(order)} workloads on Bend {releases[0]} to {releases[-1]}</title>',
           f"<style>{style}\n</style>", f'<rect class="bg" width="{W}" height="{height:.0f}"/>'] + parts + ["</svg>"]
    out_path.write_text("\n".join(svg) + "\n")
    print(out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path)
    for w in order:
        print(f"  {w:17} {pct(total[w]):>7}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
