"""scripts/report.py on a recorded run, results/2026-10-25-2.0.39 (release.sh's run of 2.0.39 against 2.0.38, 5 rounds,
1 and 16 threads, three C targets): its numbers must be the ones analyze.py wrote in that run's summary.md. Then the
same run with a GPU lane, an oracle comparison and a busy machine added."""
import shutil
import tempfile
import unittest
from pathlib import Path

from synth import ROOT, gpu_row, write_gpu
import report

RUN = ROOT / "results" / "2026-10-25-2.0.39"


def rows(text, head):
    """The table rows under a heading of a Markdown text, as lists of cells."""
    part = text.split(head, 1)[1].split("\n## ", 1)[0]
    return [[c.strip() for c in l.strip("|").split("|")] for l in part.splitlines() if l.startswith("| ")][1:]


class Report(unittest.TestCase):
    def setUp(self):
        self.text = report.report(RUN)
        self.summary = (RUN / "summary.md").read_text()

    def test_the_title_and_the_machine(self):
        self.assertTrue(self.text.startswith("# 2026-10-25-2.0.39: Bend 2.0.38 -> 2.0.39\n"))
        self.assertIn("- Machine: not busy by its load average at the start (1.40 1.30 1.03); no preflight then.",
                      self.text)
        self.assertIn("- Rounds: 5;", self.text)

    def test_the_c_ratios_are_analyze_pys(self):
        mine = {r[0]: (r[3], r[4]) for r in rows(self.text, "## Bend / C")}
        theirs = {r[0]: (r[5], r[4]) for r in rows(self.summary, "## Against the C targets")}
        self.assertEqual(mine, theirs)
        self.assertEqual(mine["softmax-ce"], ("4.85x", "4.88x"))

    def test_the_speedups_are_analyze_pys(self):
        mine = {r[0]: (r[1], r[2]) for r in rows(self.text, "## 16 threads over one")}
        theirs = {}
        for r in rows(self.summary, "## Threads"):
            theirs.setdefault(r[0], []).append(r[4])
        self.assertEqual(mine, {w: tuple(v) for w, v in theirs.items()})

    def test_the_version_changes(self):
        mine = {r[0]: r[1:] for r in rows(self.text, "## Bend 2.0.39 against 2.0.38")}
        self.assertEqual(mine["softmax-ce"], ["22152.3", "7819.2", "**-64.70%**", "**-63.24%**"])
        self.assertEqual(mine["mnist-step"][2], "**-27.15%**")
        self.assertEqual(mine["gemm-tile8"][2:], ["+0.00%", "+1.63%"])   # within the noise: not bold

    def test_a_gpu_lane_oracles_and_a_busy_machine(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "run"
            shutil.copytree(RUN, out)
            write_gpu(out, [gpu_row(r, "gemm-tile8", v, 1.0, kms=k) for r in (1, 2, 3)
                            for v, k in (("38", 20.0), ("39", 10.0))])
            (out / "oracles.txt").write_text("oracles: 33 cases, every hash is its oracle\n")
            with open(out / "env.tsv", "a") as f:
                f.write("busy\tloadavg,other_processes\n")
            text = report.report(out)
        self.assertIn("- Machine: busy (loadavg,other_processes): a diagnosis, not a result.", text)
        self.assertIn("- Oracles: oracles: 33 cases, every hash is its oracle.", text)
        self.assertEqual(rows(text, "## GPU kernels"), [["gemm-tile8", "20.0", "10.0", "**-50.00%**"]])


if __name__ == "__main__":
    unittest.main()
