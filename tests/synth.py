"""Synthetic runs.tsv files in run.sh's format, for the tests of analyze.py and scripts/chart.py."""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# what run.sh needs next to it in a copy of the repository
RUN_TOOLS = ("run.sh", "analyze.py", "scripts/oracle_diff.py", "scripts/preflight.sh", "scripts/packages.py")
# the preflight's sample of CPU 3's sibling, skipped in the tests
os.environ.setdefault("PREFLIGHT_SAMPLE", "0")


def copy_tools(d, extra=()):
    """Copies run.sh and the tools it calls (and the files in extra) into d, keeping their paths."""
    for f in RUN_TOOLS + tuple(extra):
        (Path(d) / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, Path(d) / f)


COLUMNS = ["round", "workload", "bend", "instructions", "cycles", "kinstructions", "kcycles", "seconds", "hash",
           "status", "loadavg", "threads"]


def row(rnd, workload, bend, ins, cyc, sec=1.0, hash="aaaaaaaaaaaaaaaa", status="ok", threads=1):
    return {"round": rnd, "workload": workload, "bend": bend, "instructions": ins, "cycles": cyc,
            "kinstructions": 1000, "kcycles": 1000, "seconds": f"{sec:.4f}", "hash": hash, "status": status,
            "loadavg": "0.10", "threads": threads}


def series(workload, bend, ins, cyc=None, sec=None, **kw):
    """One row per round: ins[i], cyc[i] and sec[i] are round i + 1's (cyc defaults to ins, sec to 1.0)."""
    cyc = cyc or ins
    sec = sec or [1.0] * len(ins)
    return [row(i + 1, workload, bend, a, b, s, **kw) for i, (a, b, s) in enumerate(zip(ins, cyc, sec))]


def write(path, rows):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    lines = ["\t".join(COLUMNS)] + ["\t".join(str(r[c]) for c in COLUMNS) for r in rows]
    (path / "runs.tsv").write_text("\n".join(lines) + "\n")
    return path


GPU_COLUMNS = ["round", "workload", "bend", "seconds", "kernel_ms", "kernels", "hash", "status", "loadavg"]


def gpu_row(rnd, workload, bend, sec, kms=None, kernels=100, hash="aaaaaaaaaaaaaaaa", status="ok"):
    """One line of gpu.tsv; kms=None is a run with no kernel time (nsys absent, or NSYS=0)."""
    return {"round": rnd, "workload": workload, "bend": bend, "seconds": f"{sec:.4f}",
            "kernel_ms": "" if kms is None else f"{kms:.3f}", "kernels": "" if kms is None else kernels,
            "hash": hash, "status": status, "loadavg": "0.10"}


def write_gpu(path, rows):
    path = Path(path)
    lines = ["\t".join(GPU_COLUMNS)] + ["\t".join(str(r[c]) for c in GPU_COLUMNS) for r in rows]
    (path / "gpu.tsv").write_text("\n".join(lines) + "\n")
