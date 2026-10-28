"""scripts/oracle_diff.py on synthetic runs: a run that prints every oracle passes; a differing hash, a failed run, a
workload with no oracle and a workload that did not run on a version are each listed and fail it."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from synth import row, write
import oracle_diff

ORACLES = "workload\thash\nadamw\taaaaaaaaaaaaaaaa\nsoftmax-ce\tbbbbbbbbbbbbbbbb\n"


def good():
    rows = []
    for w, h in (("adamw", "a" * 16), ("softmax-ce", "b" * 16)):
        for v in ("38", "39"):
            for t in (1, 16):
                rows.append(row(1, w, v, 1, 1, hash=h, threads=t))
        rows.append(row(1, w, "c", 1, 1, hash=h))
    return rows


class OracleDiff(unittest.TestCase):
    def run_on(self, rows):
        with tempfile.TemporaryDirectory() as d:
            out = write(Path(d) / "run", rows)
            (Path(d) / "oracles.tsv").write_text(ORACLES)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                code = oracle_diff.main(["oracle_diff.py", str(out), str(Path(d) / "oracles.tsv")])
            return code, buf.getvalue()

    def test_every_hash_its_oracle_passes(self):
        code, text = self.run_on(good())
        self.assertEqual(code, 0)
        self.assertEqual(text, "oracles: 10 cases, every hash is its oracle\n")

    def test_a_differing_hash_on_16_threads_is_listed(self):
        rows = good()
        rows[1]["hash"] = "c" * 16   # adamw, 2.0.38, 16 threads
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn(f"DIFFERS   adamw, Bend 2.0.38, 16 threads: {'c' * 16}, oracle {'a' * 16}", text)
        self.assertIn("oracles: 1 problem(s) in 10 cases", text)

    def test_a_differing_c_target_is_listed(self):
        rows = good()
        rows[4]["hash"] = "c" * 16
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn("DIFFERS   adamw, C target", text)

    def test_a_hash_that_differs_in_one_round_only_is_listed(self):
        rows = good() + [row(2, "softmax-ce", "39", 1, 1, hash="d" * 16)]
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn(f"DIFFERS   softmax-ce, Bend 2.0.39, 1 thread: {'d' * 16}", text)

    def test_a_failed_run_is_listed(self):
        rows = good() + [row(2, "adamw", "39", 1, 1, status="exit139")]
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn("FAILED    adamw, Bend 2.0.39, 1 thread: 1 run(s) ended with exit139", text)

    def test_a_workload_with_no_oracle_is_listed(self):
        rows = good() + [row(1, "gemm-tile8", "39", 1, 1)]
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn("NO ORACLE gemm-tile8, Bend 2.0.39, 1 thread", text)

    def test_a_run_with_no_runs_fails(self):
        code, text = self.run_on([])
        self.assertEqual(code, 1)
        self.assertIn("NO RUNS", text)

    def test_a_workload_that_did_not_build_on_a_version_is_listed(self):
        rows = [r for r in good() if not (r["workload"] == "softmax-ce" and r["bend"] == "38")]
        code, text = self.run_on(rows)
        self.assertEqual(code, 1)
        self.assertIn("MISSING   softmax-ce, Bend 2.0.38: no run", text)


if __name__ == "__main__":
    unittest.main()
