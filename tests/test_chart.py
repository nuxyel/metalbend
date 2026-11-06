"""scripts/chart.py's reading of the runs: the C ratios, the thread speedups, and the checks on their outputs."""
import contextlib
import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from synth import row, series, write
import chart


def runs():
    # gemm-tile8: Bend 2.0.39 at twice the C target's cycles (medians), plus rows the ratio must not read
    rows = series("gemm-tile8", 39, [10, 10, 10], cyc=[2000, 2100, 1900], sec=[1.0, 1.2, 0.9])
    rows += series("gemm-tile8", "c", [5, 5, 5], cyc=[1000, 900, 1100])
    rows += series("gemm-tile8", 38, [10, 10, 10], cyc=[9000, 9000, 9000])
    rows += series("gemm-tile8", 39, [10, 10, 10], cyc=[1, 1, 1], sec=[0.25, 0.3, 0.2], threads=16)
    rows += [row(4, "gemm-tile8", 39, "", "", sec=100.0, status="exit1")]
    # block-step: Bend only, 4x on 16 threads
    rows += series("block-step", 39, [10, 10, 10], sec=[2.0, 2.0, 2.0])
    rows += series("block-step", 39, [10, 10, 10], sec=[0.5, 0.5, 0.5], threads=16)
    return rows


class Chart(unittest.TestCase):
    def setUp(self):
        importlib.reload(chart)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs").mkdir()
        chart.ROOT = self.root
        chart.VERSION, chart.THREAD_RUN, chart.C_RUNS = "39", "run", {"gemm-tile8": "run"}

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, rows):
        write(self.root / "results" / "run", rows)

    def test_the_c_ratio_is_the_median_of_one_thread_cycles(self):
        self.put(runs())
        self.assertEqual(chart.c_ratios(), {"gemm-tile8": 2.0})
        self.assertEqual(chart.ROUNDS, {"run": 4})

    def test_a_c_target_with_other_bits_stops_the_chart(self):
        rows = [r for r in runs() if r["bend"] != "c"] + series("gemm-tile8", "c", [5, 5, 5], hash="c" * 16)
        self.put(rows)
        with self.assertRaisesRegex(AssertionError, "gemm-tile8: C and Bend outputs differ"):
            chart.c_ratios()

    def test_the_speedup_is_the_median_of_wall_times(self):
        self.put(runs())
        self.assertEqual(chart.speedups(), {"gemm-tile8": 4.0, "block-step": 4.0})

    def test_a_thread_count_with_other_bits_stops_the_chart(self):
        self.put(runs() + [row(4, "block-step", 39, 10, 10, sec=0.5, hash="d" * 16, threads=16)])
        with self.assertRaisesRegex(AssertionError, "block-step: outputs differ across thread counts"):
            chart.speedups()

    def test_main_draws_a_version_from_one_run(self):
        self.put(runs())
        argv = sys.argv
        sys.argv = ["chart.py", "39", "results/run"]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                chart.main()
        finally:
            sys.argv = argv
        svg = (self.root / "docs" / "results-2.0.39.svg").read_text()
        self.assertIn(">2.00x<", svg)
        self.assertIn(">4.00x<", svg)
        self.assertIn("Medians over 4 rounds.", svg)
        self.assertIn("Source: runs.tsv in results/run.", svg)
        self.assertIn("C ratio  gemm-tile8      2.00x", out.getvalue())

    def draw(self, version, rows, env=None):
        self.put(rows)
        if env is not None:
            (self.root / "results" / "run" / "env.tsv").write_text(f"key\tvalue\ncpu\t{env}\n")
        argv = sys.argv
        sys.argv = ["chart.py", version, "results/run", str(self.root / "out.svg")]
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                chart.main()
        finally:
            sys.argv = argv
        return (self.root / "out.svg").read_text(), out.getvalue()

    def test_a_launch_run_fifteen_c_targets_and_two_versions(self):
        # the launch run's shape: every workload with a C target, the old and the new release, 1 and 16 threads;
        # the new release's medians only, and the CPU named from env.tsv
        rows = []
        for i, w in enumerate(sorted(chart.LABELS)):
            for v, f in (("39", 3), ("40", 1)):
                rows += series(w, v, [10] * 3, cyc=[1000 * f * (i + 2)] * 3, sec=[1.0 * (i + 1)] * 3)
                rows += series(w, v, [10] * 3, cyc=[1] * 3, sec=[0.5] * 3, threads=16)
            rows += series(w, "c", [5] * 3, cyc=[1000] * 3)
        svg, out = self.draw("40", rows, env="Intel(R) Core(TM) Ultra 7 155H")
        self.assertEqual(len(chart.LABELS), 15)
        self.assertEqual(out.count("C ratio"), 15)
        self.assertEqual(out.count("16 thr"), 15)
        self.assertEqual(svg.count('<rect x="290"'), 30)
        self.assertIn("C ratio  adamw           2.00x", out)       # 2.0.40's 2x, not 2.0.39's 6x
        self.assertIn("16 thr   softmax-ce      ", out)
        self.assertIn("How far Bend 2.0.40 is from handwritten C", svg)
        self.assertIn(">Core Ultra 7 155H. One thread:", svg)
        self.assertIn("Medians over 3 rounds.", svg)

    def test_a_version_named_in_full_and_no_cpu_recorded(self):
        rows = [dict(r, bend="2.1.0") if r["bend"] == 39 else r for r in runs()]
        svg, _ = self.draw("2.1.0", rows)
        self.assertIn("How far Bend 2.1.0 is from handwritten C", svg)
        self.assertIn(">CPU not recorded. One thread:", svg)


if __name__ == "__main__":
    unittest.main()
