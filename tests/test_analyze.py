"""analyze.py on synthetic runs: what it marks beyond noise, and the outputs it flags.

    python3 -I -m unittest discover -s tests       # or: make test
"""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from synth import gpu_row, row, series, write, write_gpu
import analyze

M = 1_000_000
# 1% spread over five rounds: the median is the base, the one high round sets the spread
BASE = [1000 * M, 1000 * M, 1010 * M, 1000 * M, 1000 * M]


def scaled(xs, f):
    return [round(x * f) for x in xs]


class Analyze(unittest.TestCase):
    def summary(self, rows, gpu=None, env=None):
        with tempfile.TemporaryDirectory() as d:
            out = write(Path(d) / "run", rows)
            if gpu is not None:
                write_gpu(out, gpu)
            if env is not None:
                (out / "env.tsv").write_text("key\tvalue\n" + "".join(f"{k}\t{v}\n" for k, v in env.items()))
            with contextlib.redirect_stdout(io.StringIO()):
                analyze.main(out)
            return (out / "summary.md").read_text()

    def findings(self, rows, gpu=None):
        text = self.summary(rows, gpu)
        return text.split("## Beyond noise or differing outputs\n", 1)[1].strip().splitlines()

    def table_row(self, text, workload, bend):
        return next(l for l in text.splitlines() if l.startswith(f"| {workload} | {bend} |"))

    def test_a_move_beyond_three_spreads_is_marked(self):
        # the spread is 1% on both sides, so 3.5% is beyond 3x the noise
        rows = series("w", 39, BASE) + series("w", 38, scaled(BASE, 1.035))
        text = self.summary(rows)
        self.assertIn("**+3.50%**", self.table_row(text, "w", "2.0.38"))
        f = self.findings(rows)
        self.assertIn("- w: 2.0.38 instructions +3.50% against 2.0.39 (noise 1.00%)", f)
        self.assertIn("- w: 2.0.38 cycles +3.50% against 2.0.39 (noise 1.00%)", f)

    def test_a_move_within_three_spreads_is_not(self):
        # 2.5% is more than twice the noise but less than three times
        rows = series("w", 39, BASE) + series("w", 38, scaled(BASE, 1.025))
        text = self.summary(rows)
        self.assertIn("| +2.50% | +2.50% |", self.table_row(text, "w", "2.0.38"))
        self.assertNotIn("**", self.table_row(text, "w", "2.0.38"))
        self.assertEqual(self.findings(rows), ["None."])

    def test_a_drop_is_marked_as_a_rise_is(self):
        rows = series("w", 39, BASE) + series("w", 38, scaled(BASE, 0.96))
        self.assertIn("- w: 2.0.38 instructions -4.00% against 2.0.39 (noise 1.00%)", self.findings(rows))

    def test_the_noise_is_the_larger_spread_of_the_two(self):
        # the newest version repeats exactly; the older one's 1% spread is the noise
        rows = series("w", 39, [1000 * M] * 5) + series("w", 38, scaled(BASE, 1.025))
        self.assertEqual(self.findings(rows), ["None."])

    def test_the_spread_is_max_minus_min_over_the_median(self):
        # median 1000, mean 1060: (1200 - 1000) / 1000 is 20%, over the mean it would be 18.87%
        skewed = [1000 * M, 1000 * M, 1000 * M, 1100 * M, 1200 * M]
        text = self.summary(series("w", 39, skewed))
        self.assertIn("| w | 2.0.39 | 1000.0 | 20.00% | 1000.0 | 20.00% |", text)

    def test_the_floors(self):
        # no spread at all: 0.2% of instructions is within the 0.1% floor's 3x, 0.4% beyond; cycles keep a 1% floor
        flat = [1000 * M] * 5
        self.assertEqual(self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.002))), ["None."])
        f = self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.004)))
        self.assertEqual(f, ["- w: 2.0.38 instructions +0.40% against 2.0.39 (noise 0.10%)"])
        f = self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.035)))
        self.assertIn("- w: 2.0.38 cycles +3.50% against 2.0.39 (noise 1.00%)", f)
        f = self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.025)))
        self.assertEqual([l for l in f if "cycles" in l], [])

    def test_fewer_than_three_rounds_mark_nothing(self):
        flat = [1000 * M] * 2
        self.assertEqual(self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.5))), ["None."])
        flat = [1000 * M] * 3
        self.assertIn("- w: 2.0.38 instructions +50.00% against 2.0.39 (noise 0.10%)",
                      self.findings(series("w", 39, flat) + series("w", 38, scaled(flat, 1.5))))

    def test_the_newest_version_is_the_base(self):
        rows = series("w", 37, scaled(BASE, 1.1)) + series("w", 39, BASE) + series("w", 38, BASE)
        f = self.findings(rows)
        self.assertIn("- w: 2.0.37 instructions +10.00% against 2.0.39 (noise 1.00%)", f)
        self.assertFalse([l for l in f if "2.0.38" in l])

    def test_versions_in_release_order(self):
        # 2.0.9 before 2.0.10 (not as strings), and a version after 2.0 named in full, newer than every 2.0.x
        rows = series("w", "9", BASE) + series("w", "10", BASE) + series("w", "2.1.0", scaled(BASE, 1.1))
        text = self.summary(rows)
        self.assertIn("Changes are against Bend 2.1.0;", text)
        lines = [l for l in text.splitlines() if l.startswith("| w |")]
        self.assertEqual([l.split(" | ")[1] for l in lines], ["2.0.9", "2.0.10", "2.1.0"])
        self.assertIn("- w: 2.0.10 instructions -9.09% against 2.1.0 (noise 1.00%)", self.findings(rows))

    def test_a_differing_hash_is_a_finding(self):
        rows = series("w", 39, BASE) + series("w", 38, BASE, hash="bbbbbbbbbbbbbbbb")
        self.assertEqual(self.findings(rows),
                         ["- w: 2.0.38's output differs from 2.0.39's (bbbbbbbbbbbbbbbb against aaaaaaaaaaaaaaaa)"])

    def test_two_hashes_across_rounds_are_a_finding(self):
        rows = series("w", 39, BASE) + series("w", 38, BASE[:4]) + [row(5, "w", 38, BASE[4], BASE[4], hash="b" * 16)]
        self.assertIn("- w: 2.0.38 printed 2 different outputs across its rounds", self.findings(rows))

    def test_a_failed_run_is_counted_not_averaged(self):
        rows = series("w", 39, BASE) + series("w", 38, BASE[:4]) + [row(5, "w", 38, "", "", status="exit1")]
        text = self.summary(rows)
        self.assertIn("(+1 failed)", self.table_row(text, "w", "2.0.38"))
        self.assertEqual(self.findings(rows), ["None."])

    def test_a_version_that_did_not_build(self):
        rows = series("w", 39, BASE) + series("v", 39, BASE) + series("v", 38, BASE)
        self.assertIn("| w | 2.0.38 | - | - | - | - | - | - | - | no build |", self.summary(rows))

    def test_the_c_target(self):
        half = scaled(BASE, 0.5)
        text = self.summary(series("w", 39, BASE) + series("w", "c", half, sec=[0.25] * 5))
        self.assertIn("| w | 500.0 | 500.0 | 0.250 | 2.00x | 2.00x | 4.00x | yes |", text)
        self.assertEqual(text.split("## Beyond noise or differing outputs\n", 1)[1].strip(), "None.")
        f = self.findings(series("w", 39, BASE) + series("w", "c", half, hash="c" * 16))
        self.assertEqual(f, ["- w: the C target's output differs from Bend 2.0.39's"])

    def test_threads(self):
        one = series("w", 39, BASE, sec=[1.0] * 5)
        many = series("w", 39, BASE, sec=[0.25] * 5, threads=16)
        text = self.summary(one + many)
        self.assertIn("| w | 2.0.39 | 1.000 | 0.250 | 4.00x | yes |", text)
        # the 16-thread runs stay out of the one-thread medians and spreads
        self.assertIn("| w | 2.0.39 | 1000.0 | 1.00% | 1000.0 | 1.00% | 1.000 |", text)

    def test_a_thread_count_that_prints_other_bits_is_a_finding(self):
        rows = series("w", 39, BASE) + series("w", 39, BASE, hash="d" * 16, threads=16)
        text = self.summary(rows)
        self.assertIn("| 1.00x | **no** |", text)
        self.assertEqual(self.findings(rows), ["- w: 2.0.39 prints different outputs across thread counts"])

    def gpu_section(self, text):
        return text.split("## GPU targets", 1)[1].split("## Beyond noise", 1)[0]

    def test_no_gpu_table_without_gpu_runs(self):
        self.assertNotIn("## GPU targets", self.summary(series("w", 39, BASE)))

    def test_the_gpu_target(self):
        # wall times 2.0, 2.0, 2.2 (median 2.0, spread 10%); kernel times 50, 51, 50 ms over 120 kernels
        gpu = [gpu_row(1, "w", 39, 2.0, 50.0, 120), gpu_row(2, "w", 39, 2.2, 51.0, 120), gpu_row(3, "w", 39, 2.0, 50.0, 120)]
        text = self.summary(series("w", 39, BASE), gpu)
        self.assertIn("| w | 2.0.39 | 2.000 | 10.00% | 50.0 | 2.00% | 120 | aaaaaaaaaaaaaaaa | yes |", text)
        self.assertEqual(self.findings(series("w", 39, BASE), gpu), ["None."])
        # its rows stay out of the CPU's tables
        self.assertIn("| w | 2.0.39 | 1000.0 | 1.00% | 1000.0 | 1.00% | 1.000 |", text)

    def test_a_gpu_run_without_kernel_time(self):
        text = self.summary(series("w", 39, BASE), [gpu_row(1, "w", 39, 2.0)])
        self.assertIn("| w | 2.0.39 | 2.000 | 0.00% | - | - | - | aaaaaaaaaaaaaaaa | yes |", text)

    def test_a_gpu_output_other_than_the_cpus_is_a_finding(self):
        gpu = [gpu_row(1, "w", 39, 2.0, 50.0, hash="e" * 16)]
        self.assertIn("| **no** |", self.gpu_section(self.summary(series("w", 39, BASE), gpu)))
        self.assertEqual(self.findings(series("w", 39, BASE), gpu),
                         ["- w: the GPU target's output differs from the CPU's on 2.0.39"])

    def test_gpu_rounds_that_print_two_outputs_are_a_finding(self):
        gpu = [gpu_row(1, "w", 39, 2.0, 50.0), gpu_row(2, "w", 39, 2.0, 50.0, hash="e" * 16)]
        f = self.findings(series("w", 39, BASE), gpu)
        self.assertIn("- w: the GPU target on 2.0.39 printed 2 different outputs across its rounds", f)

    def test_a_gpu_output_that_changes_between_versions_is_a_finding(self):
        rows = series("w", 39, BASE) + series("w", 38, BASE)
        gpu = [gpu_row(1, "w", 39, 2.0, 50.0), gpu_row(1, "w", 38, 2.0, 50.0, hash="e" * 16)]
        f = self.findings(rows, gpu)
        self.assertIn("- w: the GPU target's output on 2.0.38 differs from 2.0.39's (eeeeeeeeeeeeeeee against "
                      "aaaaaaaaaaaaaaaa)", f)

    def test_a_failed_gpu_run_is_counted_not_averaged(self):
        gpu = [gpu_row(1, "w", 39, 2.0, 50.0), gpu_row(2, "w", 39, 9.0, status="exit1")]
        self.assertIn("| w | 2.0.39 | 2.000 | 0.00% | 50.0 | 0.00% | 100 | aaaaaaaaaaaaaaaa (+1 failed) | yes |",
                      self.summary(series("w", 39, BASE), gpu))
        gpu = [gpu_row(1, "w", 39, 9.0, status="exit1")]
        self.assertIn("| w | 2.0.39 | - | - | - | - | - | failed | - |", self.summary(series("w", 39, BASE), gpu))

    def test_the_machine_state_is_a_table(self):
        text = self.summary(series("w", 39, BASE), env={"cpu": "Fake CPU", "governor": "powersave", "busy": "no"})
        self.assertIn("| cpu | Fake CPU |", text)
        self.assertIn("| governor | powersave |", text)
        self.assertIn("| thp | - |", text)
        self.assertNotIn("busy run", text)

    def test_a_busy_run_is_marked(self):
        text = self.summary(series("w", 39, BASE), env={"busy": "loadavg,other_processes"})
        self.assertTrue(text.startswith("# run\n\n**A busy run** (loadavg,other_processes): "), text[:200])

    def test_a_run_from_before_the_preflight_is_judged_by_its_load(self):
        self.assertIn("**A busy run** (loadavg)", self.summary(series("w", 39, BASE), env={"loadavg_start": "2.5 1 1"}))
        self.assertNotIn("busy run", self.summary(series("w", 39, BASE), env={"loadavg_start": "0.4 1 1"}))
        self.assertNotIn("busy run", self.summary(series("w", 39, BASE)))

    def test_a_run_with_no_rounds(self):
        self.assertIn("No one-thread Bend runs in runs.tsv.", self.summary([]))


if __name__ == "__main__":
    unittest.main()
