"""scripts/track_verdict.py on synthetic counts: the thresholds (instructions beyond 0.1%, D1 misses beyond 5%), each
verdict, the issue written only for a regression, a mixed change or a changed output, and the files it writes."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from synth import ROOT  # noqa: F401 (puts scripts/ on the path)
import track_verdict as tv

HEAD = "ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"


def count(ref, w, ir, d1, ll=10, bits="ok", hash="a" * 16):
    commit = "1" * 40 if ref == "v2.0.39" else "2" * 40
    if bits in ("compile-failed", "run-failed"):
        ir = d1 = ll = hash = "-"
    return f"{ref}\t{commit}\t{ref[1:]}\t{w}\t{ir}\t{d1}\t{ll}\t{hash}\t{bits}\t18.1.3\t3.22.0"


def pair(w, ir, d1, ir2, d12, bits2="ok"):
    return [count("v2.0.39", w, ir, d1), count("v2.0.40", w, ir2, d12, bits=bits2)]


class Judge(unittest.TestCase):
    def verdict(self, ir, d1, ir2, d12, bits2="ok", bits1="ok"):
        old = {"ir": str(ir), "d1_misses": str(d1), "bits": bits1, "hash": "a" * 16}
        new = {"ir": str(ir2), "d1_misses": str(d12), "bits": bits2, "hash": "b" * 16}
        return tv.judge(old, new)[0]

    def test_instructions_beyond_a_tenth_of_a_percent(self):
        self.assertEqual(self.verdict(1_000_000, 100, 1_001_001, 100), "regression")
        self.assertEqual(self.verdict(1_000_000, 100, 1_001_000, 100), "same")
        self.assertEqual(self.verdict(1_000_000, 100, 998_999, 100), "improvement")
        self.assertEqual(self.verdict(1_000_000, 100, 999_000, 100), "same")

    def test_d1_misses_beyond_five_percent(self):
        self.assertEqual(self.verdict(1000, 1_000_000, 1000, 1_050_001), "regression")
        self.assertEqual(self.verdict(1000, 1_000_000, 1000, 1_050_000), "same")
        self.assertEqual(self.verdict(1000, 1_000_000, 1000, 949_999), "improvement")

    def test_one_up_one_down_is_mixed(self):
        # bpe-encode's two upstream changes would read this way if one had lowered the instructions instead
        self.assertEqual(self.verdict(1_000_000, 1_000_000, 990_000, 2_000_000), "mixed")

    def test_a_changed_output_or_a_broken_build_is_bits(self):
        self.assertEqual(self.verdict(1000, 10, 1000, 10, bits2="DIFF"), "bits")
        self.assertEqual(self.verdict(1000, 10, 1000, 10, bits2="compile-failed"), "bits")
        self.assertEqual(self.verdict(1000, 10, 1000, 10, bits2="run-failed"), "bits")

    def test_an_old_bend_that_cannot_count_is_no_baseline(self):
        self.assertEqual(self.verdict(1000, 10, 1000, 10, bits1="compile-failed"), "no-baseline")

    def test_a_missing_side(self):
        self.assertEqual(tv.judge(None, {"bits": "ok"})[0], "missing")

    def test_shown(self):
        self.assertEqual(tv.shown(0.0933), "+9.33%")
        self.assertEqual(tv.shown(-0.012), "-1.20%")
        self.assertEqual(tv.shown(1.02), "2.02x")
        self.assertEqual(tv.shown(-0.6), "0.40x")


class Files(unittest.TestCase):
    def run_on(self, lines, *extra):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        (d / "counts.tsv").write_text("\n".join([HEAD] + lines) + "\n")
        out = d / "out"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = tv.main([str(d / "counts.tsv"), "v2.0.39", "v2.0.40", str(out), *extra])
        return code, out, buf.getvalue()

    def tearDown(self):
        self.tmp.cleanup()

    def test_bpe_encode_the_way_2_0_40_moved_it(self):
        lines = pair("bpe-encode", 177_706_500_000, 1_107_100_000, 194_274_800_000, 2_241_700_000)
        lines += pair("adamw", 16_825_554_909, 50_000_000, 16_600_000_000, 50_000_000)
        lines += pair("read-native", 587_572_467, 9_435_978, 587_572_467, 9_435_978)
        code, out, printed = self.run_on(lines, "--run", "https://example.invalid/run/1",
                                         "--store", "track/runs/x/")
        self.assertEqual(code, 0)
        rows = (out / "verdict.tsv").read_text().splitlines()
        self.assertEqual(rows[0].split("\t"), tv.COLUMNS)
        by = {r.split("\t")[0]: r.split("\t") for r in rows[1:]}
        self.assertEqual(by["bpe-encode"][1], "regression")
        self.assertEqual(by["adamw"][1], "improvement")
        self.assertEqual(by["read-native"][1], "same")
        self.assertIn("instructions +9.32%, D1 misses 2.02x", by["bpe-encode"][-1])
        self.assertIn("2 of 3 workloads moved", printed)
        title = (out / "issue-title.txt").read_text()
        self.assertEqual(title, "Bend v2.0.40: regression in 1 workload against v2.0.39\n")
        issue = (out / "issue.md").read_text()
        self.assertIn("| bpe-encode | +9.32% | 2.02x | its oracle | regression |", issue)
        self.assertIn("scripts/count.sh v2.0.39 bpe-encode\nscripts/count.sh v2.0.40 bpe-encode", issue)
        self.assertIn("Improvements in the same run: adamw (instructions -1.34%).", issue)
        self.assertIn("https://example.invalid/run/1", issue)
        self.assertNotIn("read-native", issue)
        self.assertIn("track/runs/x/", (out / "report.md").read_text())

    def test_improvements_alone_write_no_issue(self):
        code, out, printed = self.run_on(pair("adamw", 1000, 10, 900, 10))
        self.assertEqual(code, 0)
        self.assertFalse((out / "issue.md").exists())
        self.assertIn("none written", printed)

    def test_a_changed_output_writes_an_issue(self):
        code, out, _ = self.run_on(pair("softmax-ce", 1000, 10, 1000, 10, bits2="DIFF"))
        self.assertIn("bits in 1 workload", (out / "issue-title.txt").read_text())

    def test_a_row_of_another_ref_is_refused(self):
        code, out, _ = self.run_on([count("v2.0.38", "adamw", 1, 1)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
