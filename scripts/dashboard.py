"""The dashboard: a static site drawn from the repository's raw files and the data branch; no number is typed in here.

    python3 -I scripts/dashboard.py <data> <out>             # <data>: the data branch's files; <out>: the site
    python3 -I scripts/dashboard.py <data> <out> <results>   # release runs from another folder than results/

It reads:
- `results/<date>-<version>/` (release.sh's runs, on my machine): one-thread instructions and cycles, Bend / C, the
  speedup on the run's most threads and the GPU targets' kernel time, medians as scripts/report.py takes them. A
  version measured by two release runs is shown from the newer one.
- `history/` on the data branch (its newest folder): every workload's Cachegrind counts on every release.
- `track/` on the data branch: the release watch's comparisons and the bisects in `track/regressions/`.
- `docs/upstream.tsv`: the upstream issue I filed for a bisect's finding, where there is one.
- `workloads/<name>/`: its README, whether it has a C and a GPU target; `oracles.tsv`.

It writes `index.html` (Bend / C, the corpus at a glance, the history, the release watch, the bisects, how it
measures and its limits), `w/<workload>.html` (one workload over the releases, then its README) and `style.css`
(scripts/dashboard.css). Charts are inline SVG and HTML in the colors of scripts/history_chart.py, with a tooltip on
every mark; light and dark follow the reader's setting. Standard library only.
"""
import csv
import html
import math
import re
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from analyze import full, machine, vkey  # noqa: E402
from chart import LABELS  # noqa: E402
from history_chart import bounds  # noqa: E402
from history_report import version_key  # noqa: E402
from track_verdict import D1_LIMIT, IR_LIMIT  # noqa: E402

REPO = "https://github.com/nuxyel/metalbend"
RELEASE_RUN = re.compile(r"^\d{4}-\d{2}-\d{2}-(\d+\.\d+\.\d+)$")
METRIC = {"ir": "instructions", "d1": "simulated D1 misses", "bits": "the output"}
MINUS = "−"


# ---------------------------------------------------------------- reading

def read(path):
    path = Path(path)
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def keyval(path):
    return {r["key"]: r["value"] for r in read(path)}


def release_run(d):
    """One release run's medians by (workload, full version): instructions and cycles on one thread, Bend / C in both,
    the wall-time speedup on the run's most threads over one, the GPU kernel time; the same numbers as report.py's."""
    med = statistics.median
    ins, cyc, wall, gpu = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    for r in read(d / "runs.tsv"):
        if r["status"] != "ok" or not r["instructions"].isdigit():
            continue
        t = int(r.get("threads") or 1)
        wall[(r["workload"], r["bend"], t)].append(float(r["seconds"]))
        if t == 1:
            ins[(r["workload"], r["bend"])].append(int(r["instructions"]))
            cyc[(r["workload"], r["bend"])].append(int(r["cycles"]))
    for r in read(d / "gpu.tsv"):
        if r["status"] == "ok" and r["kernel_ms"]:
            gpu[(r["workload"], r["bend"])].append(float(r["kernel_ms"]))
    many = max((t for _, _, t in wall), default=1)
    cells = {}
    for (w, b), xs in ins.items():
        if b == "c":
            continue
        cell = {"run": d.name, "ins": med(xs), "cyc": med(cyc[(w, b)]), "rounds": len(xs)}
        if (w, "c") in ins:
            cell["c_cyc"] = cell["cyc"] / med(cyc[(w, "c")])
            cell["c_ins"] = cell["ins"] / med(ins[(w, "c")])
        if many > 1 and wall.get((w, b, 1)) and wall.get((w, b, many)):
            cell["speedup"] = med(wall[(w, b, 1)]) / med(wall[(w, b, many)])
        if gpu.get((w, b)):
            cell["gpu_ms"] = med(gpu[(w, b)])
        cells[(w, full(b))] = cell
    _, busy = machine(d)
    return {"name": d.name, "env": keyval(d / "env.tsv"), "busy": busy, "threads": many, "cells": cells}


def state(run):
    """The machine's state during a release run, as scripts/report.py words it."""
    if run["busy"] != "no":
        return f"busy ({run['busy']}): a diagnosis"
    return "idle by the preflight" if "busy" in run["env"] else "not busy by its load average; no preflight then"


def real_counts(results):
    """Every release run in results/, oldest first, and their cells merged so a newer run's version wins."""
    runs = [release_run(d) for d in sorted(Path(results).iterdir())
            if RELEASE_RUN.match(d.name) and (d / "runs.tsv").exists()]
    cells = {}
    for run in runs:
        cells.update(run["cells"])
    versions = sorted({v for _, v in cells}, key=vkey)
    return runs, cells, versions


def history(data):
    """The newest history folder: its releases and counts by (workload, release)."""
    index = read(data / "history" / "index.tsv")
    if not index:
        return None
    row = index[-1]
    folder = data / "history" / row["folder"]
    counts = read(folder / "counts.tsv")
    h = {"row": row, "folder": row["folder"], "ir": {}, "d1": {}, "bits": {},
         "releases": sorted({r["ref"] for r in counts}, key=version_key),
         "steps": read(folder / "steps.tsv"), "gaps": read(folder / "gaps.tsv"),
         "env": [keyval(p) for p in sorted((folder / "env").glob("*.tsv"))],
         "clang": sorted({r["clang"] for r in counts if r.get("clang")}),
         "valgrind": sorted({r["valgrind"] for r in counts if r.get("valgrind")})}
    for r in counts:
        k = (r["workload"], r["ref"])
        h["bits"][k] = r["bits"]
        if r["ir"].isdigit():
            h["ir"][k] = int(r["ir"])
            h["d1"][k] = int(r["d1_misses"])
    return h


def track(data):
    """The release watch's comparisons, newest first, each with its verdicts and env."""
    rows = read(data / "track" / "index.tsv")
    for r in rows:
        folder = data / "track" / "runs" / r["folder"]
        r["verdicts"] = read(folder / "verdict.tsv")
        r["env"] = keyval(folder / "env.tsv")
    last = data / "track" / "last-tag"
    return rows[::-1], (last.read_text().strip() if last.exists() else "")


def bisects(data):
    out = []
    for p in sorted((data / "track" / "regressions").glob("*/report.tsv")):
        rep = keyval(p)
        rep["folder"] = p.parent.name
        out.append(rep)
    return sorted(out, key=lambda r: (version_key(r.get("bad", "v0")), r.get("workload", "")), reverse=True)


def upstream():
    return {r["regression"]: r["issue"] for r in read(ROOT / "docs" / "upstream.tsv")}


def workloads():
    """Each workload: its label, its README split at the first section (the intro, then the rest), its C and GPU
    targets, its oracles."""
    oracles = {r["workload"]: r["hash"] for r in read(ROOT / "oracles.tsv")}
    out = {}
    for d in sorted((ROOT / "workloads").iterdir()):
        if not (d / "main.bend").exists():
            continue
        text = (d / "README.md").read_text() if (d / "README.md").exists() else ""
        text = re.sub(r"\A# [^\n]*\n", "", text)          # the title: the page has its own
        intro, _, rest = text.partition("\n## ")
        out[d.name] = {"label": LABELS.get(d.name, d.name), "intro": intro.strip(),
                       "rest": ("## " + rest).strip() if rest else "",
                       "c": (d / "native.c").exists(), "gpu": (d / "gpu.bend").exists(),
                       "oracle": oracles.get(d.name, ""), "gpu_oracle": oracles.get(f"{d.name}:gpu", "")}
    return out


# ---------------------------------------------------------------- formatting

def esc(s):
    return html.escape(str(s), quote=True)


def inline(md, w):
    """A README paragraph's Markdown to HTML: code, bold and links (relative ones to the file on GitHub)."""
    s = esc(md)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        url = html.unescape(m.group(2))
        if not re.match(r"https?://", url):
            url = f"{REPO}/blob/main/workloads/{w}/{url}"
        return f'<a href="{esc(url)}">{m.group(1)}</a>'
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)


def markdown(text, w):
    """A workload README's Markdown to HTML: its sections (one level below the page's), paragraphs, lists, tables
    and code blocks; what a README here uses, nothing more."""
    out = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append(f"<pre><code>{esc(chr(10).join(lines[i + 1:j]))}</code></pre>")
            i = j + 1
        elif line.startswith("#"):
            level = min(4, len(line) - len(line.lstrip("#")) + 1)
            out.append(f"<h{level}>{inline(line.lstrip('#').strip(), w)}</h{level}>")
            i += 1
        elif line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            cells = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[i:j]]
            body = [r for r in cells[1:] if not all(set(c) <= set("-: ") for c in r)]
            out.append(table([inline(c, w) for c in cells[0]], [[inline(c, w) for c in r] for r in body]))
            i = j
        elif re.match(r"[-*] ", line):
            items = []
            while i < len(lines) and lines[i].strip() and (re.match(r"[-*] ", lines[i]) or lines[i].startswith("  ")):
                if re.match(r"[-*] ", lines[i]):
                    items.append(lines[i][2:].strip())
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(t, w)}</li>" for t in items) + "</ul>")
        else:
            j = i
            while j < len(lines) and lines[j].strip() and not re.match(r"(#|\||```|[-*] )", lines[j]):
                j += 1
            out.append(f"<p>{inline(' '.join(l.strip() for l in lines[i:j]), w)}</p>")
            i = j
    return "\n".join(out)


def num(n):
    return f"{int(round(n)):,}"


def minus(s):
    return s.replace("-", MINUS)


def ratio(x):
    """Bend / C and speedups: two decimals under 10x, one under 100x, none above."""
    return f"{x:.2f}x" if x < 10 else f"{x:.1f}x" if x < 100 else f"{x:.0f}x"


def move(r):
    """A change as a new/old ratio: a factor when it halves or doubles, a percentage otherwise."""
    if r <= 0.5 or r >= 2:
        return f"{r:.2f}x"
    c = 100 * (r - 1)
    return "0%" if abs(c) < 0.005 else minus(f"{c:+.2f}%")


def direction(r, limit):
    return "fewer" if r < 1 - limit else "more" if r > 1 + limit else ""


def short(ref):
    return ref.lstrip("v")


def sha(c):
    return f'<a href="https://github.com/bendlang/bend/commit/{esc(c)}"><code>{esc(c[:8])}</code></a>'


def data_url(path):
    return f"{REPO}/blob/data/{path}"


def latest_date(*dates):
    ds = sorted(d[:10] for d in dates if d and re.match(r"\d{4}-\d{2}-\d{2}", d))
    return ds[-1] if ds else ""


# ---------------------------------------------------------------- charts

def spark(series, releases, unit, limit, what):
    """A small line chart of one workload's count on every release, relative to the first release it is counted on,
    on its own scale (scripts/history_chart.py's bounds): a triangle where it moved beyond the limit, a band where it
    is not counted. Every point has a tooltip with the count."""
    counted = [r for r in releases if series.get(r)]
    if not counted:
        return ""
    base = series[counted[0]]
    rel = {r: (series[r] / base if series.get(r) else None) for r in releases}
    W, H, L, R, T, B = 300, 128, 40, 12, 10, 22
    x0, x1, top, bot = L, W - R, T, H - B
    sx = (lambda k: x0 + (x1 - x0) * k / (len(releases) - 1)) if len(releases) > 1 else (lambda k: (x0 + x1) / 2)
    lo, hi = bounds([v for v in rel.values() if v is not None])
    sy = lambda v: bot - (bot - top) * (v - lo) / (hi - lo)
    half = (x1 - x0) / max(1, len(releases) - 1) / 2
    p = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(what)}">']
    k = 0
    while k < len(releases):
        if rel[releases[k]] is None:
            j = k
            while j + 1 < len(releases) and rel[releases[j + 1]] is None:
                j += 1
            a, b = max(x0, sx(k) - half), min(x1, sx(j) + half)
            p.append(f'<rect x="{a:.1f}" y="{top}" width="{b - a:.1f}" height="{bot - top}" class="s-gap">'
                     f'<title>not counted on {esc(", ".join(short(r) for r in releases[k:j + 1]))}</title></rect>')
            k = j
        k += 1
    for g in (lo, 1, hi):
        y = sy(g)
        if (g == hi and sy(1) - y < 11) or (g == lo and y - sy(1) < 11):
            continue  # too close to 0% to label
        p.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="{"s-base" if g == 1 else "s-grid"}"/>')
        p.append(f'<text x="{x0 - 5}" y="{y + 3.3:.1f}" class="s-tick" text-anchor="end">'
                 f'{minus(f"{100 * (g - 1):+.0f}%").replace("+0%", "0%")}</text>')
    pts = [(sx(k), sy(rel[r])) for k, r in enumerate(releases) if rel[r] is not None]
    p.append('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" class="s-line"/>')
    prev = None
    for k, r in enumerate(releases):
        v = rel[r]
        if v is None:
            prev = None
            continue
        x, y = sx(k), sy(v)
        tip = f"{short(r)}: {num(series[r])} {unit}"
        if r != counted[0]:
            tip += f", {move(v)} against {short(counted[0])}"
        if prev is not None and abs(v / prev - 1) > limit:
            tip += f"; {move(v / prev)} from the release before"
            if v < prev:
                mark = f'<polygon points="{x - 5:.1f},{y - 4:.1f} {x + 5:.1f},{y - 4:.1f} {x:.1f},{y + 5:.1f}" class="s-down"/>'
            else:
                mark = f'<polygon points="{x - 5:.1f},{y + 4:.1f} {x + 5:.1f},{y + 4:.1f} {x:.1f},{y - 5:.1f}" class="s-up"/>'
        else:
            mark = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.2" class="s-dot"/>'
        p.append(f'<g class="s-pt"><title>{esc(tip)}</title><circle cx="{x:.1f}" cy="{y:.1f}" r="9" class="s-hit"/>'
                 f"{mark}</g>")
        prev = v
    step = 1 if len(releases) <= 10 else 2
    for k, r in enumerate(releases):
        if k % step == 0 or k == len(releases) - 1:
            p.append(f'<text x="{sx(k):.1f}" y="{H - 6}" class="s-tick" text-anchor="middle">'
                     f'{esc(r.rsplit(".", 1)[-1])}</text>')
    p.append("</svg>")
    return "".join(p)


def total_change(series, releases):
    counted = [r for r in releases if series.get(r)]
    return series[counted[-1]] / series[counted[0]] if len(counted) > 1 else None


def bend_c_chart(cells, versions, rows):
    """Bend / C in cycles, one row a workload with a C target, every version measured as a dot on a log scale; the
    newest version filled, the one before it gray, older ones hollow."""
    vals = [cells[(w, v)]["c_cyc"] for w in rows for v in versions if "c_cyc" in cells.get((w, v), {})]
    if not vals:
        return ""
    lo = min(1.0, 10 ** math.floor(math.log10(min(vals))))
    hi = next(t for t in (2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10 ** 4, 10 ** 5) if t >= max(vals))
    pos = lambda x: 100 * (math.log10(x) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
    ticks = [t for t in (0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10 ** 4)
             if lo <= t <= hi and (hi < 100 or t in (0.1, 0.5, 1, 2, 5, 10, 100, 1000, 10 ** 4))]
    style = {versions[-1]: "now"}
    if len(versions) > 1:
        style[versions[-2]] = "prev"
    key = "".join(f'<span><i class="dot {style.get(v, "old")}"></i>{esc(v)}</span>' for v in versions)
    out = [f'<div class="key">{key}</div>', '<div class="dumb">']
    grid = "".join(f'<i class="gl" style="left:{pos(t):.2f}%"></i>' for t in ticks)
    for w in rows:
        have = [(v, cells[(w, v)]) for v in versions if "c_cyc" in cells.get((w, v), {})]
        xs = [pos(c["c_cyc"]) for _, c in have]
        dots = "".join(
            f'<i class="dot {style.get(v, "old")}" style="left:{pos(c["c_cyc"]):.2f}%" '
            f'title="{esc(w)} on Bend {esc(v)}: {ratio(c["c_cyc"])} C\'s cycles ({ratio(c["c_ins"])} its instructions), '
            f'results/{esc(c["run"])}"></i>' for v, c in have)
        span = f'<i class="span" style="left:{min(xs):.2f}%;width:{max(xs) - min(xs):.2f}%"></i>' if len(xs) > 1 else ""
        now = have[-1][1]["c_cyc"] if have else None
        out.append(f'<div class="row"><a class="lbl" href="w/{esc(w)}.html">{esc(LABELS.get(w, w))}'
                   f'<span class="name">{esc(w)}</span></a><div class="track">{grid}{span}{dots}</div>'
                   f'<div class="val">{ratio(now) if now else ""}</div></div>')
    labels = "".join(f'<span style="left:{pos(t):.2f}%">{t:g}x</span>' for t in ticks)
    out.append(f'<div class="axis"><div class="pad"></div><div class="ticks">{labels}</div><div></div></div></div>')
    return "\n".join(out)


# ---------------------------------------------------------------- pages

def page(title, body, depth=0, description=""):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def table(head, rows, numeric=()):
    th = "".join(f'<th{" class=n" if i in numeric else ""}>{h}</th>' for i, h in enumerate(head))
    trs = "".join("<tr>" + "".join(f'<td{" class=n" if i in numeric else ""}>{c}</td>' for i, c in enumerate(r))
                  + "</tr>" for r in rows)
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def changed(r, limit, text=None):
    d = direction(r, limit)
    t = text or move(r)
    return f'<span class="{d}">{t}</span>' if d else t


def fn(name):
    """A C function's name without the program's hash: WL_FID_0x559a..._main_bump_go -> main_bump_go."""
    return re.sub(r"0[xX][0-9a-fA-F]{8,}_?", "", name).removeprefix("WL_FID_") or name


def bisect_list(reps, ups, depth=0):
    """Each bisect as one item: what moved, the commit and its pull request, the functions, the report and the issue."""
    items = []
    for rep in reps:
        metric = rep.get("metric", "")
        step = rep.get("step_change", "")
        try:
            r = float(step[:-1]) if step.endswith("x") else 1 + float(step.rstrip("%")) / 100
        except ValueError:
            r = 1.0
        what = "" if metric == "bits" else "fewer" if r < 1 else "more"
        head = (f'<a href="{"../" * depth}w/{esc(rep["workload"])}.html"><code>{esc(rep["workload"])}</code></a>, '
                f'{esc(METRIC.get(metric, metric))}, {esc(short(rep.get("good", "")))} to {esc(short(rep.get("bad", "")))}')
        if rep.get("decided") == "yes" and rep.get("first_bad"):
            found = (f'<span class="{what}">{esc(minus(step))}</span> at {sha(rep["first_bad"])}, '
                     f'<a href="{esc(rep["pr_url"])}">bendlang/bend#{esc(rep["pr"])}</a> '
                     f'({esc(rep.get("pr_title") or rep.get("subject", ""))}); '
                     f'{esc(minus(rep.get("range_change", "")))} over the range of {esc(rep.get("commits", ""))} commits.')
        else:
            found = f'not decided between {esc(rep.get("candidates", ""))}.'
        moved = rep.get("functions_moved", "").split()
        extra = f' The functions that moved: {", ".join(f"<code>{esc(fn(f))}</code>" for f in moved[:4])}.' if moved else ""
        issue = ups.get(rep["folder"])
        links = (f'<a href="{esc(data_url(f"track/regressions/{rep["folder"]}/report.md"))}">The report</a>'
                 + (f'; I filed <a href="https://github.com/bendlang/bend/issues/{esc(issue)}">bendlang/bend#{esc(issue)}</a>'
                    if issue else "") + ".")
        items.append(f"<li><strong>{head}</strong>: {found}{extra} {links}</li>")
    return '<ul class="findings">' + "".join(items) + "</ul>"


def build(data, out, results=ROOT / "results"):
    data, out = Path(data), Path(out)
    runs, cells, versions = real_counts(results)
    h = history(data)
    comparisons, last_tag = track(data)
    reps = bisects(data)
    ups = upstream()
    ws = workloads()
    out.mkdir(parents=True, exist_ok=True)
    (out / "w").mkdir(exist_ok=True)
    shutil.copy(ROOT / "scripts" / "dashboard.css", out / "style.css")
    (out / ".nojekyll").write_text("")

    newest = runs[-1] if runs else None
    rel = h["releases"] if h else []
    dates = [r["env"].get("date", "") for r in runs] + [c["env"].get("date", "") for c in comparisons]
    dates += [e.get("date", "") for e in (h["env"] if h else [])]
    asof = latest_date(*dates)
    cpu = newest["env"].get("cpu", "").replace("(R)", "").replace("(TM)", "").replace("Intel ", "") if newest else ""
    gpu = newest["env"].get("gpu", "").split(",")[0].replace("NVIDIA ", "") if newest else ""
    runner_clang = h["clang"] if h else []
    runner_vg = h["valgrind"] if h else []

    # ---- index
    b = [f"<h1>MetalBend</h1>",
         f'<p class="lede">A corpus of {len(ws)} real machine-learning workloads for Bend 2\'s compiler, cut from my '
         "three Bend projects (bend-ml, llama.bend and BendTorch) and run on every Bend release. Each workload prints a "
         "hash of its whole output, which must be its oracle; most have a handwritten C twin with the same order of "
         "operations and the same bits, so the distance from Bend to native code is a ratio.</p>",
         f'<p class="meta">Data as of {esc(asof)}. Drawn by <code>scripts/dashboard.py</code> from the raw files: '
         f'<a href="{REPO}/tree/main/results">results/</a> on main (my machine) and the '
         f'<a href="{REPO}/tree/data">data branch</a> (GitHub\'s runners). '
         f'<a href="{REPO}">The repository</a>, <a href="{REPO}#readme">its README</a>. Renan Vinícius (@nuxyel).</p>']

    natives = [w for w in ws if ws[w]["c"]]
    now = versions[-1] if versions else ""
    natives.sort(key=lambda w: (cells.get((w, now), {}).get("c_cyc", float("inf")), w))
    b.append("<h2>Bend against C</h2>")
    if natives and now:
        b.append(f"<p>CPU cycles of Bend's build over the C twin's, one pinned thread on my machine ({esc(cpu)}), on "
                 "every release my release runs measured; 1x would be C's speed. Each version comes from the newest "
                 "release run that measured it: " +
                 "; ".join(f'<a href="{REPO}/tree/main/results/{esc(r["name"])}">{esc(r["name"])}</a>'
                           f' ({" and ".join(sorted({v for _, v in r["cells"]}, key=vkey))}, {esc(state(r))})'
                           for r in runs) +
                 ". Hover a dot for its numbers.</p>")
        b.append(bend_c_chart(cells, versions, natives))
        far = [w for w in natives if cells.get((w, now), {}).get("c_cyc", 0) >= 10]
        if far:
            b.append("<p>" + "; ".join(
                f'<a href="w/{esc(w)}.html"><code>{esc(w)}</code></a> is {ratio(cells[(w, now)]["c_cyc"])} on {esc(now)}'
                for w in far) + ": their pages say why.</p>")

    b.append("<h2>The corpus at a glance</h2>")
    rows = []
    for w in sorted(ws):
        c_first = next((v for v in versions if "c_cyc" in cells.get((w, v), {})), None)
        c_now = cells.get((w, now), {}).get("c_cyc")
        sp = cells.get((w, now), {}).get("speedup")
        hist = total_change({r: h["ir"].get((w, r)) for r in rel}, rel) if h else None
        since = next((r for r in rel if h["ir"].get((w, r))), None) if h else None
        last = next((v for c in comparisons for v in c["verdicts"] if v["workload"] == w), None)
        rows.append([f'<a href="w/{esc(w)}.html"><code>{esc(w)}</code></a><br><span class="meta">{esc(ws[w]["label"])}</span>',
                     f'{ratio(cells[(w, c_first)]["c_cyc"])} <span class="meta">{esc(c_first)}</span>'
                     if c_first and c_first != now else "",
                     ratio(c_now) if c_now else "-",
                     ratio(sp) if sp else "-",
                     (changed(hist, IR_LIMIT) + f' <span class="meta">from {esc(short(since))}</span>') if hist else "-",
                     (esc(last["verdict"]) + (f'<br><span class="meta">{esc(minus(last["why"]))}</span>' if last["why"] else ""))
                     if last else "-"])
    threads = newest["threads"] if newest else ""
    b.append(f"<p>Bend / C in cycles on my machine on the first release measured (where it is not {esc(now)}) and on "
             f"{esc(now)}; the speedup on {threads} threads over one on {esc(now)} (wall time); instructions under "
             f"Cachegrind from the first release of the history each workload builds on to {esc(short(rel[-1]) if rel else '')}; "
             "the newest verdict of the release watch.</p>")
    b.append(table(["workload", "Bend / C, first", f"Bend / C, {esc(now)}", f"{threads} threads",
                    "instructions (runner)", "release watch"], rows, numeric={1, 2, 3}))

    if h:
        n_ok = sum(1 for v in h["bits"].values() if v == "ok")
        n_diff = sum(1 for v in h["bits"].values() if v == "DIFF")
        order = sorted(ws, key=lambda w: (total_change({r: h["ir"].get((w, r)) for r in rel}, rel) or 1, w))
        b.append(f"<h2>The history: Bend {esc(short(rel[0]))} to {esc(short(rel[-1]))}</h2>")
        b.append(f"<p>Every workload's instructions on every release from {esc(short(rel[0]))} to {esc(short(rel[-1]))}, "
                 "counted under Cachegrind on one GitHub runner a workload (every release of a workload in one job, so a "
                 "line compares with itself), against the first release the workload builds on, each on its own scale. "
                 f"{n_ok} counts; " + ("every output was its oracle" if not n_diff else f"{n_diff} outputs were not their oracle") +
                 f"; {len(h['gaps'])} release{'s' if len(h['gaps']) != 1 else ''} where a workload does not build. "
                 f'The counts: <a href="{esc(data_url(f"history/{h["folder"]}/counts.tsv"))}">history/{esc(h["folder"])}</a>.</p>')
        b.append('<div class="key"><span><i class="mark down"></i>fewer instructions than the release before '
                 f'(beyond {100 * IR_LIMIT:g}%)</span><span><i class="mark up"></i>more</span>'
                 '<span><i class="mark gap"></i>does not build</span></div>')
        cards = []
        for w in order:
            s = {r: h["ir"].get((w, r)) for r in rel}
            t = total_change(s, rel)
            cards.append(f'<a class="card" href="w/{esc(w)}.html"><div class="head"><span class="t">{esc(ws[w]["label"])}'
                         f'<br><span class="name">{esc(w)}</span></span><span class="v">'
                         f'{changed(t, IR_LIMIT) if t else ""}</span></div>'
                         f'{spark(s, rel, "instructions", IR_LIMIT, f"{w}: instructions on Bend {rel[0]} to {rel[-1]}")}</a>')
        b.append('<div class="cards">' + "".join(cards) + "</div>")

    b.append("<h2>The release watch</h2>")
    b.append("<p>Once a day a workflow looks for a release of bendlang/bend after the last one it compared "
             f"(<code>{esc(last_tag)}</code> now). On one, it builds that release and the one before it from source "
             "and counts every workload with both under Cachegrind in one job, so the two counts share a runner. A "
             f"workload is a finding when its instructions move beyond {100 * IR_LIMIT:g}%, its simulated D1 misses "
             f"beyond {100 * D1_LIMIT:g}%, or its output is not its oracle; a regression opens an issue in the "
             "repository and is bisected. Nothing is posted on bendlang/bend by the workflow.</p>")
    rows = []
    for c in comparisons:
        v = defaultdict(int)
        for x in c["verdicts"]:
            v[x["verdict"]] += 1
        rows.append([esc(c["folder"][:10]), f'{esc(short(c["old"]))} to {esc(short(c["new"]))}', esc(c["trigger"]),
                     str(len(c["verdicts"])),
                     ", ".join(f"{n} {esc(k)}{'s' if n > 1 and k not in ('same', 'bits') else ''}"
                               for k, n in sorted(v.items())),
                     f'<a href="{esc(data_url(f"track/runs/{c["folder"]}/report.md"))}">report</a> · '
                     f'<a href="{esc(c["run"])}">run</a>'])
    b.append(table(["date", "compared", "trigger", "workloads", "verdicts", ""], rows, numeric={3}))

    if reps:
        b.append("<h2>What the bisect found</h2>")
        b.append("<p>Each finding bisected over bendlang/bend's commits between the two releases: every step a source "
                 "build of Bend at that commit and one Cachegrind count of the workload. The report names the first "
                 "commit where the count moved, its pull request, the functions that moved and the C that changed. "
                 "Where I filed an issue upstream, it is linked.</p>")
        b.append(bisect_list(reps, ups))

    b.append("<h2>How it measures</h2><ul>")
    if newest:
        rounds = max((c["rounds"] for c in newest["cells"].values()), default=0)
        b.append(f"<li><strong>My machine</strong> ({esc(cpu)}{', ' + esc(gpu) if gpu else ''}): at each release, "
                 f"the release and the one before it, built from their tags, and every C twin, {rounds} rounds in a "
                 "shuffled order; one thread pinned to one core, user-mode instructions and cycles from perf, medians; "
                 f"{newest['threads']} threads by the wall clock; the GPU targets by the device's kernel time under "
                 "nsys.</li>")
    b.append("<li><strong>GitHub's runners</strong>: Cachegrind's exact instruction count of one thread and its "
             f"simulated caches (valgrind {esc(', '.join(runner_vg))}, clang {esc(', '.join(runner_clang))}). A "
             "count compares with another taken in the same job, never with my machine's.</li>"
             "<li><strong>The bits</strong>: every run and count records the hash of the output; one that is not "
             "the oracle is a finding, never noise.</li></ul>")

    b.append("<h2>Limits</h2><ul>")
    b.append("<li>The runners' caches are simulated, with no prefetcher, so a cache change shows on another scale "
             "than on hardware.")
    bpe = next((r for r in reps if r.get("metric") == "d1"), None)
    if bpe:
        w, old, new = bpe["workload"], short(bpe["good"]), short(bpe["bad"])
        a, z = cells.get((w, old)), cells.get((w, new))
        if a and z:
            b.append(f" <code>{esc(w)}</code> on {esc(new)}: {esc(bpe['range_change'])} the simulated D1 misses on "
                     f"the runner, {esc(minus(move(z['cyc'] / a['cyc'])))} cycles on my machine.")
    b.append("</li>")
    b.append(f"<li>Real cycles exist for the releases my release runs measured ({esc(', '.join(versions))}); before "
             "them the history is the runner's instruction counts.</li>")
    b.append(f"<li>{newest['threads'] if newest else 'Many'} threads and the GPU are measured only on my machine; "
             "the runners count one thread and have no GPU.</li>")
    for w in sorted({g["workload"] for g in (h["gaps"] if h else [])}):
        gs = [g for g in h["gaps"] if g["workload"] == w]
        b.append(f"<li><code>{esc(w)}</code> does not build on {esc(', '.join(short(g['release']) for g in gs))} "
                 f"({esc(', '.join(sorted({g['bits'] for g in gs})))}; recorded, not adapted).</li>")
    b.append("</ul>")
    (out / "index.html").write_text(page("MetalBend", "\n".join(b), 0,
                                         f"{len(ws)} ML workloads for Bend's compiler on every Bend release: Bend "
                                         "against C, the history, the release watch and what the bisect found."))

    # ---- one page a workload
    for w, info in ws.items():
        b = [f'<p class="crumb"><a href="../index.html">MetalBend</a> / <code>{esc(w)}</code></p>',
             f'<h1>{esc(info["label"])}</h1><p class="name">{esc(w)}</p>',
             markdown(info["intro"], w),
             f'<p class="meta"><a href="{REPO}/tree/main/workloads/{esc(w)}">workloads/{esc(w)}</a> · '
             f'C twin: {"yes" if info["c"] else "no"} · GPU target: {"yes" if info["gpu"] else "no"} · '
             f'oracle <code>{esc(info["oracle"])}</code>'
             + (f', on the GPU <code>{esc(info["gpu_oracle"])}</code>' if info["gpu_oracle"] else "") + "</p>"]
        mine = [(v, cells[(w, v)]) for v in versions if (w, v) in cells]
        b.append("<h2>On my machine</h2>")
        if mine:
            rows = [[esc(v), f'<a href="{REPO}/tree/main/results/{esc(c["run"])}">{esc(c["run"])}</a>',
                     num(c["ins"] / 1e6), num(c["cyc"] / 1e6),
                     ratio(c["c_cyc"]) if "c_cyc" in c else "-", ratio(c["c_ins"]) if "c_ins" in c else "-",
                     ratio(c["speedup"]) if "speedup" in c else "-",
                     f'{c["gpu_ms"]:.1f}' if "gpu_ms" in c else "-"] for v, c in mine]
            b.append("<p>Medians of the release run, one thread pinned to one core, user mode; the speedup is "
                     "wall time on the run's most threads over one; the GPU column is the device's kernel time.</p>")
            b.append(table(["Bend", "run", "M instructions", "M cycles", "Bend / C cycles", "Bend / C instructions",
                            f"{newest['threads'] if newest else ''} threads", "GPU ms"], rows,
                           numeric={2, 3, 4, 5, 6, 7}))
            if len(mine) > 1:
                (v0, a), (v1, z) = mine[-2], mine[-1]
                if a["run"] == z["run"]:
                    b.append(f"<p>{esc(v1)} against {esc(v0)} in the same run: instructions "
                             f"{changed(z['ins'] / a['ins'], 0.001)}, cycles {changed(z['cyc'] / a['cyc'], 0.01)}. "
                             f'Whether a change is beyond noise is in the run\'s <a href="{REPO}/blob/main/results/'
                             f'{esc(z["run"])}/report.md">report</a>.</p>')
        else:
            b.append("<p>No release run has measured it yet.</p>")

        if h and any(h["bits"].get((w, r)) for r in rel):
            b.append(f"<h2>On the runners, Bend {esc(short(rel[0]))} to {esc(short(rel[-1]))}</h2>")
            ir = {r: h["ir"].get((w, r)) for r in rel}
            d1 = {r: h["d1"].get((w, r)) for r in rel}
            b.append(f"<p>Cachegrind's counts on every release, against the first release it builds on, each chart on "
                     f"its own scale; a triangle where a count moved beyond the release watch's threshold "
                     f"({100 * IR_LIMIT:g}% for instructions, {100 * D1_LIMIT:g}% for D1 misses).</p>")
            b.append('<div class="pair">'
                     f'<div class="card"><div class="head"><span class="t">Instructions</span><span class="v">'
                     f'{changed(total_change(ir, rel), IR_LIMIT) if total_change(ir, rel) else ""}</span></div>'
                     f'{spark(ir, rel, "instructions", IR_LIMIT, f"{w}: instructions")}</div>'
                     f'<div class="card"><div class="head"><span class="t">Simulated D1 misses</span><span class="v">'
                     f'{changed(total_change(d1, rel), D1_LIMIT) if total_change(d1, rel) else ""}</span></div>'
                     f'{spark(d1, rel, "D1 misses", D1_LIMIT, f"{w}: simulated D1 misses")}</div></div>')
            steps = {(s["new"]): s for s in h["steps"] if s["workload"] == w}
            rows = []
            for r in rel:
                s = steps.get(r)
                bits = h["bits"].get((w, r), "")
                verdict = s["verdict"] if s else ""
                rows.append([esc(short(r)),
                             num(ir[r]) if ir[r] else "-", num(d1[r]) if d1[r] else "-",
                             changed(1 + float(s["ir_change"]), IR_LIMIT) if s and s["ir_change"] not in ("", "-") else "",
                             changed(1 + float(s["d1_change"]), D1_LIMIT) if s and s["d1_change"] not in ("", "-") else "",
                             esc(verdict), "its oracle" if bits == "ok" else esc(bits)])
            b.append(table(["release", "instructions", "D1 misses", "Δ instructions", "Δ D1 misses", "step", "output"],
                           rows, numeric={1, 2, 3, 4}))
            for g in (g for g in h["gaps"] if g["workload"] == w):
                b.append(f'<p class="meta">{esc(short(g["release"]))}: {esc(g["bits"])}, <code>{esc(g["why"])}</code></p>')

        watch = [(c, v) for c in comparisons for v in c["verdicts"] if v["workload"] == w]
        if watch:
            b.append("<h2>The release watch</h2>")
            rows = [[esc(c["folder"][:10]), f'{esc(short(c["old"]))} to {esc(short(c["new"]))}',
                     changed(1 + float(v["ir_change"]), IR_LIMIT) if v["ir_change"] not in ("", "-") else "-",
                     changed(1 + float(v["d1_change"]), D1_LIMIT) if v["d1_change"] not in ("", "-") else "-",
                     esc(v["verdict"]),
                     f'<a href="{esc(data_url(f"track/runs/{c["folder"]}/report.md"))}">report</a>'] for c, v in watch]
            b.append(table(["date", "compared", "instructions", "D1 misses", "verdict", ""], rows, numeric={2, 3}))

        mine_reps = [r for r in reps if r.get("workload") == w]
        if mine_reps:
            b.append("<h2>Bisects</h2>")
            b.append(bisect_list(mine_reps, ups, depth=1))
        if info["rest"]:
            b.append("<h2>The workload</h2>")
            b.append(markdown(info["rest"], w))
        (out / "w" / f"{w}.html").write_text(page(f"{info['label']}: MetalBend", "\n".join(b), 1,
                                                  f"MetalBend's {w} workload on every Bend release."))
    return out


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    out = build(argv[1], argv[2], *(argv[3:] or []))
    print(out / "index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
