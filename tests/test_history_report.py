"""scripts/history_report.py on synthetic counts: the steps judged as the release watch judges two Bends, a workload
that builds only from a later release (gap, then first), the per-release table and each workload's change from its
first release to its last."""
import contextlib
import csv
import io
import sys
import tempfile
import unittest
from pathlib import Path

from synth import ROOT  # noqa: F401 (puts scripts/ on the path)
import history_report as hr

HEAD = "ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"


def count(rel, w, ir, d1=100, bits="ok"):
    if bits in ("compile-failed", "run-failed"):
        ir = d1 = "-"
    return f"{rel}\t{'1' * 40}\t{rel[1:]}\t{w}\t{ir}\t{d1}\t10\t{'a' * 16}\t{bits}\t18.1.3\t3.22.0"


class Report(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.d = Path(self.tmp.name)
        rows = [count("v2.0.9", "adamw", 1000), count("v2.0.10", "adamw", 900), count("v2.0.11", "adamw", 900),
                count("v2.0.9", "read", 0, bits="compile-failed"), count("v2.0.10", "read", 0, bits="compile-failed"),
                count("v2.0.11", "read", 500, d1=300)]
        (d / "counts.tsv").write_text("\n".join([HEAD] + rows) + "\n")
        (d / "gaps.tsv").write_text("release\tworkload\tbits\twhy\nv2.0.9\tread\tcompile-failed\terror: old ABI\n"
                                    "v2.0.10\tread\tcompile-failed\terror: old ABI\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.run_main(), 0)

    def run_main(self):
        argv, sys.argv = sys.argv, ["history_report.py", str(self.d)]
        try:
            return hr.main()
        finally:
            sys.argv = argv

    def tearDown(self):
        self.tmp.cleanup()

    def tsv(self, name):
        with open(self.d / name) as f:
            return list(csv.DictReader(f, delimiter="\t"))

    def test_releases_in_version_order(self):
        self.assertEqual([(s["old"], s["new"]) for s in self.tsv("steps.tsv") if s["workload"] == "adamw"],
                         [("v2.0.9", "v2.0.10"), ("v2.0.10", "v2.0.11")])

    def test_the_verdicts(self):
        v = {(s["workload"], s["new"]): s["verdict"] for s in self.tsv("steps.tsv")}
        self.assertEqual(v, {("adamw", "v2.0.10"): "improvement", ("adamw", "v2.0.11"): "same",
                             ("read", "v2.0.10"): "gap", ("read", "v2.0.11"): "first"})

    def test_coverage_names_the_reason(self):
        cov = {c["workload"]: c for c in self.tsv("coverage.tsv")}
        self.assertEqual(cov["read"]["v2.0.9"], "compile-failed: error: old ABI")
        self.assertEqual(cov["read"]["v2.0.11"], "ok")

    def test_the_report(self):
        md = (self.d / "report.md").read_text()
        self.assertIn("| v2.0.10 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | adamw -10.00% |", md)
        self.assertIn("| adamw | v2.0.9 | 1,000 | 900 | -10.00% |", md)
        self.assertNotIn("| read | v2.0.11 |", md)   # one release counted: no change to show
        self.assertIn("- read: v2.0.9, v2.0.10 (compile-failed: error: old ABI)", md)


if __name__ == "__main__":
    unittest.main()
