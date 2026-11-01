"""The numbers a release run gives the launch, from its raw files (runs.tsv, gpu.tsv, env.tsv, oracles.txt):

    python3 -I scripts/report.py results/<date>-2.0.40          # Markdown on stdout

For the newest version of the run against the one before it (both from release.sh): each workload's change in
user-mode instructions and cycles on one thread (medians, marked beyond noise as analyze.py marks it); Bend / C in
cycles and instructions for every workload with a C target, on both versions; the wall-time speedup of 16 threads over
one; and, with a gpu.tsv, the GPU targets' kernel time on the device. On top: whether every hash was its oracle
(oracles.txt) and whether the machine was busy (env.tsv). Nothing is typed in: every number is read from the run.
"""
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analyze import full, machine, spread, vkey  # noqa: E402


def read(path):
    with open(path) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def change(new, old, floor):
    """The change from old to new medians, and whether it is beyond noise (3x the larger spread, a floor, 3 rounds)."""
    d = statistics.median(new) / statistics.median(old) - 1
    noise = max(spread(new), spread(old), floor)
    return d, min(len(new), len(old)) >= 3 and abs(d) > 3 * noise


def pct(d, beyond):
    s = f"{d * 100:+.2f}%"
    return f"**{s}**" if beyond else s


def report(out):
    out = Path(out)
    runs = [r for r in read(out / "runs.tsv") if r["status"] == "ok" and r["instructions"].isdigit()]
    one = defaultdict(lambda: {"ins": [], "cyc": []})
    wall = defaultdict(list)
    for r in runs:
        t = int(r.get("threads") or 1)
        wall[(r["workload"], r["bend"], t)].append(float(r["seconds"]))
        if t == 1:
            one[(r["workload"], r["bend"])]["ins"].append(int(r["instructions"]))
            one[(r["workload"], r["bend"])]["cyc"].append(int(r["cycles"]))
    versions = sorted({v for _, v in one if v != "c"}, key=vkey)
    if not versions:
        return f"# {out.name}\n\nNo one-thread Bend runs in runs.tsv.\n"
    new, old = versions[-1], (versions[-2] if len(versions) > 1 else None)
    workloads = sorted({w for w, _ in one})
    _, busy = machine(out)
    env = {r["key"]: r["value"] for r in read(out / "env.tsv")} if (out / "env.tsv").exists() else {}
    if busy != "no":
        state = f"busy ({busy}): a diagnosis, not a result"
    elif "busy" in env:
        state = "idle by the preflight"
    else:
        state = f"not busy by its load average at the start ({env.get('loadavg_start', '?')}); no preflight then"
    oracles = (out / "oracles.txt").read_text().strip().splitlines() if (out / "oracles.txt").exists() else []
    title = f"Bend {full(old)} -> {full(new)}" if old else f"Bend {full(new)}"
    lines = [f"# {out.name}: {title}", "",
             f"- Machine: {state}.",
             f"- Oracles: {oracles[-1] if oracles else 'no oracles.txt (run.sh did not reach its end)'}."]
    rounds = max(len(c["ins"]) for c in one.values())
    lines.append(f"- Rounds: {rounds}; medians throughout; **bold** is beyond noise.")

    if old:
        lines += ["", f"## Bend {full(new)} against {full(old)} (one thread, user mode)", "",
                  f"| workload | {full(old)} Minstr | {full(new)} Minstr | Δ instr | Δ cycles |",
                  "|---|---:|---:|---:|---:|"]
        for w in workloads:
            a, b = one.get((w, old)), one.get((w, new))
            if not a or not b:
                lines.append(f"| {w} | {'-' if not a else ''} | {'-' if not b else ''} | - | - |")
                continue
            di = change(b["ins"], a["ins"], 0.001)
            dc = change(b["cyc"], a["cyc"], 0.01)
            lines.append(f"| {w} | {statistics.median(a['ins']) / 1e6:.1f} | {statistics.median(b['ins']) / 1e6:.1f} | "
                         f"{pct(*di)} | {pct(*dc)} |")

    natives = [w for w in workloads if (w, "c") in one]
    if natives:
        vs = [v for v in (old, new) if v]
        head = " | ".join(f"{full(v)} cycles | {full(v)} instr" for v in vs)
        lines += ["", "## Bend / C (one thread, user mode)", "", f"| workload | {head} |",
                  "|---|" + "---:|---:|" * len(vs)]
        for w in natives:
            c = one[(w, "c")]
            cols = []
            for v in vs:
                b = one.get((w, v))
                cols += ([f"{statistics.median(b['cyc']) / statistics.median(c['cyc']):.2f}x",
                          f"{statistics.median(b['ins']) / statistics.median(c['ins']):.2f}x"] if b else ["-", "-"])
            lines.append(f"| {w} | " + " | ".join(cols) + " |")

    many = sorted({t for _, _, t in wall if t > 1})
    if many:
        t = many[-1]
        vs = [v for v in (old, new) if v]
        lines += ["", f"## {t} threads over one (wall time)", "",
                  "| workload | " + " | ".join(full(v) for v in vs) + " |", "|---|" + "---:|" * len(vs)]
        for w in workloads:
            cols = []
            for v in vs:
                a, b = wall.get((w, v, 1)), wall.get((w, v, t))
                cols.append(f"{statistics.median(a) / statistics.median(b):.2f}x" if a and b else "-")
            lines.append(f"| {w} | " + " | ".join(cols) + " |")

    if (out / "gpu.tsv").exists():
        kms = defaultdict(list)
        for r in read(out / "gpu.tsv"):
            if r["status"] == "ok" and r["kernel_ms"]:
                kms[(r["workload"], r["bend"])].append(float(r["kernel_ms"]))
        vs = [v for v in (old, new) if v]
        lines += ["", "## GPU kernels (ms on the device, nsys)", "",
                  "| workload | " + " | ".join(full(v) for v in vs) + (" | Δ |" if old else " |"),
                  "|---|" + "---:|" * (len(vs) + (1 if old else 0))]
        for w in sorted({w for w, _ in kms}):
            cols = [f"{statistics.median(kms[(w, v)]):.1f}" if kms.get((w, v)) else "-" for v in vs]
            if old:
                a, b = kms.get((w, old)), kms.get((w, new))
                cols.append(pct(*change(b, a, 0.01)) if a and b else "-")
            lines.append(f"| {w} | " + " | ".join(cols) + " |")
    return "\n".join(lines) + "\n"


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    sys.stdout.write(report(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
