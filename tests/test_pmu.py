"""scripts/pmu.sh on fake PMU trees (a hybrid Intel CPU, a machine with one `cpu` PMU), and run.sh with stand-ins for
perf and taskset: a one-thread run is pinned to CPU (3 unless set) and counted by that CPU's PMU, a run on more threads
sums the instructions of every PMU. The probes source the same file."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT, copy_tools
from test_run_guard import FAKE_BEND

# perf stat -x, -o <file> -e <events> <cmd...>: logs its events, writes a count per event (instructions/u 100 per PMU,
# cycles/u 200, instructions/k 3, cycles/k 4) in perf's CSV format, and runs the command
FAKE_PERF = """#!/usr/bin/env python3
import os, subprocess, sys
a = sys.argv[1:]
out, ev = a[a.index("-o") + 1], a[a.index("-e") + 1]
cmd = a[a.index("-e") + 2:]
open(os.environ["FAKE_LOG"], "a").write("perf " + ev + "\\n")
counts = {"instructions/u": 100, "cycles/u": 200, "instructions/k": 3, "cycles/k": 4}
with open(out, "w") as f:
    for e in ev.split(","):
        f.write(f"{counts[e.split('/', 1)[1]]},,{e},1000,100.00,,\\n")
sys.exit(subprocess.run(cmd).returncode)
"""
FAKE_TASKSET = """#!/bin/sh
echo "taskset $1 $2" >> "$FAKE_LOG"
shift 2
exec "$@"
"""


def pmu_tree(d, hybrid):
    """A /sys/bus/event_source/devices of its own: cpu_core (CPUs 0-11) and cpu_atom (12-19,22), or one `cpu`."""
    dev = Path(d) / "devices"
    for name, cpus in ((("cpu_core", "0-11"), ("cpu_atom", "12-19,22")) if hybrid else (("cpu", "0-7"),)):
        (dev / name).mkdir(parents=True)
        (dev / name / "cpus").write_text(cpus + "\n")
    return dev


def pmu(dev, mode, cpu=None):
    env = dict(os.environ, PMU_DEVICES=str(dev))
    env.pop("CPU", None)
    if cpu is not None:
        env["CPU"] = cpu
    p = subprocess.run(["bash", "-c", f'. "{ROOT}/scripts/pmu.sh"; echo "$CPU"; echo "$PMU_ONE"; pmu_events {mode}'],
                       env=env, capture_output=True, text=True, check=True)
    return p.stdout.split()


class Detect(unittest.TestCase):
    def test_a_hybrid_cpu_counts_a_p_core_with_cpu_core(self):
        with tempfile.TemporaryDirectory() as d:
            dev = pmu_tree(d, hybrid=True)
            self.assertEqual(pmu(dev, "one"), ["3", "cpu_core", "cpu_core/instructions/u,cpu_core/cycles/u,"
                                                                "cpu_core/instructions/k,cpu_core/cycles/k"])
            self.assertEqual(pmu(dev, "many")[2], "cpu_core/instructions/u,cpu_atom/instructions/u,cpu_core/cycles/u,"
                                                  "cpu_core/instructions/k,cpu_core/cycles/k")

    def test_an_e_core_is_counted_with_cpu_atom(self):
        with tempfile.TemporaryDirectory() as d:
            dev = pmu_tree(d, hybrid=True)
            for cpu in ("12", "17", "22"):
                self.assertEqual(pmu(dev, "one", cpu)[:2], [cpu, "cpu_atom"], cpu)
            self.assertEqual(pmu(dev, "one", "20")[1], "cpu_core")

    def test_one_pmu_is_plain_cpu(self):
        with tempfile.TemporaryDirectory() as d:
            dev = pmu_tree(d, hybrid=False)
            self.assertEqual(pmu(dev, "one", "5"), ["5", "cpu", "cpu/instructions/u,cpu/cycles/u,cpu/instructions/k,"
                                                                "cpu/cycles/k"])
            self.assertEqual(pmu(dev, "many")[2], "cpu/instructions/u,cpu/cycles/u,cpu/instructions/k,cpu/cycles/k")


class RunSh(unittest.TestCase):
    def run_sh(self, hybrid, threads="1", **env):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            copy_tools(d)
            (d / "oracles.tsv").write_text("workload\thash\nblock-step\t4355a46b19d348dc\n")
            (d / "workloads" / "block-step").mkdir(parents=True)
            (d / "workloads" / "block-step" / "main.bend").write_text("")
            (d / "data").mkdir()
            (d / "data" / "dense.bin").write_bytes(b"")
            bin_ = d / "bin"
            bin_.mkdir()
            for name, body in (("bend", FAKE_BEND), ("perf", FAKE_PERF), ("taskset", FAKE_TASKSET)):
                (bin_ / name).write_text(body)
                (bin_ / name).chmod(0o755)
            log = d / "log"
            log.write_text("")
            env = dict(os.environ, BEND_99=str(bin_ / "bend"), VERSIONS="99", WORKLOADS="block-step", THREADS=threads,
                       ROUNDS="1", OUT="results/t", FAKE_LOG=str(log), PMU_DEVICES=str(pmu_tree(d, hybrid)),
                       PATH=f"{bin_}:{os.environ['PATH']}", **env)
            p = subprocess.run(["bash", str(d / "run.sh")], env=env, capture_output=True, text=True, timeout=120)
            self.assertIn("summary.md", " ".join(os.listdir(d / "results" / "t")), p.stderr)
            runs = (d / "results" / "t" / "runs.tsv").read_text().splitlines()
            head = runs[0].split("\t")
            rows = [dict(zip(head, r.split("\t"))) for r in runs[1:]]
            envtsv = dict(l.split("\t", 1) for l in (d / "results" / "t" / "env.tsv").read_text().splitlines()[1:])
            summary = (d / "results" / "t" / "summary.md").read_text()
            return log.read_text().splitlines(), rows, envtsv, summary

    def test_one_thread_is_pinned_to_cpu_3_and_counted_by_cpu_core(self):
        log, rows, env, _ = self.run_sh(hybrid=True)
        self.assertIn("taskset -c 3", log)
        self.assertIn("perf cpu_core/instructions/u,cpu_core/cycles/u,cpu_core/instructions/k,cpu_core/cycles/k", log)
        self.assertEqual((rows[0]["instructions"], rows[0]["cycles"], rows[0]["kinstructions"], rows[0]["kcycles"]),
                         ("100", "200", "3", "4"))
        self.assertEqual((env["cpu_pinned"], env["pmu"]), ("3", "cpu_core (one thread); cpu_core cpu_atom (more)"))

    def test_cpu_moves_the_pin_and_a_plain_pmu_counts(self):
        log, rows, env, summary = self.run_sh(hybrid=False, CPU="5")
        self.assertIn("taskset -c 5", log)
        self.assertNotIn("taskset -c 3", log)
        self.assertIn("perf cpu/instructions/u,cpu/cycles/u,cpu/instructions/k,cpu/cycles/k", log)
        self.assertEqual((rows[0]["instructions"], rows[0]["cycles"]), ("100", "200"))
        self.assertEqual(env["cpu_pinned"], "5")
        self.assertIn("pre_cpu5_sibling", env)
        self.assertIn("| pre_cpu5_sibling |", summary)

    def test_more_threads_sum_both_pmus(self):
        log, rows, _, _ = self.run_sh(hybrid=True, threads="16")
        self.assertIn("perf cpu_core/instructions/u,cpu_atom/instructions/u,cpu_core/cycles/u,cpu_core/instructions/k,"
                      "cpu_core/cycles/k", log)
        self.assertEqual([(r["threads"], r["instructions"], r["cycles"]) for r in rows], [("16", "200", "200")])
        self.assertFalse([l for l in log if l.startswith("taskset")])


class Probes(unittest.TestCase):
    def test_count_sh_pins_to_cpu_and_counts_with_its_pmu(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            bin_ = d / "bin"
            bin_.mkdir()
            for name, body in (("perf", FAKE_PERF), ("taskset", FAKE_TASKSET), ("prog", "#!/bin/sh\necho 1\n")):
                (bin_ / name).write_text(body)
                (bin_ / name).chmod(0o755)
            log = d / "log"
            log.write_text("")
            env = dict(os.environ, ROUNDS="1", CPU="6", FAKE_LOG=str(log), PMU_DEVICES=str(pmu_tree(d, False)),
                       PATH=f"{bin_}:{os.environ['PATH']}")
            p = subprocess.run(["bash", str(ROOT / "probes" / "1781" / "count.sh"), str(bin_ / "prog")], env=env,
                               capture_output=True, text=True, timeout=30)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(log.read_text().splitlines(),
                             ["taskset -c 6", "perf cpu/instructions/u,cpu/cycles/u,cpu/instructions/k"])
            self.assertEqual(p.stdout.splitlines()[1].split("\t")[:5], ["prog", "1", "100", "200", "3"])

    def test_the_l3_probe_pins_to_cpu_and_counts_with_its_pmu(self):
        # it needs E-cores that share the L3 and its antagonist, so only its text is checked here
        text = (ROOT / "probes" / "l3" / "run.sh").read_text()
        self.assertIn('. "$root/scripts/pmu.sh"', text)
        self.assertIn('taskset -c "$CPU" perf stat', text)
        self.assertIn("$PMU_ONE/mem_load_retired.l3_miss/u", text)
        self.assertNotIn("cpu_core/", text)
        self.assertNotIn("taskset -c 3 ", text)


if __name__ == "__main__":
    unittest.main()
