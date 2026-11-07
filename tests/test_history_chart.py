"""scripts/history_chart.py on synthetic counts: one chart a workload ordered by its change, the change labeled, a
band where a workload does not build, a triangle where a count moved beyond 0.1%, and a line below the floor cut."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

HEAD = "ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"


def count(rel, w, ir, bits="ok"):
    ir = "-" if bits != "ok" else ir
    return f"{rel}\t{'1' * 40}\t{rel[1:]}\t{w}\t{ir}\t100\t10\t{'a' * 16}\t{bits}\t18.1.3\t3.22.0"


class Chart(unittest.TestCase):
    def draw(self, rows):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "counts.tsv").write_text("\n".join([HEAD] + rows) + "\n")
            p = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "history_chart.py"), str(d),
                                str(d / "h.svg")], capture_output=True, text=True, timeout=60)
            self.assertEqual(p.returncode, 0, p.stderr)
            return (d / "h.svg").read_text(), p.stdout

    def test_order_labels_and_marks(self):
        svg, out = self.draw([count("v2.0.9", "adamw", 1000), count("v2.0.10", "adamw", 900),
                              count("v2.0.11", "adamw", 900),
                              count("v2.0.9", "read-bf16", 0, "compile-failed"), count("v2.0.10", "read-bf16", 500),
                              count("v2.0.11", "read-bf16", 510)])
        self.assertEqual([line.split()[0] for line in out.splitlines()[1:]], ["adamw", "read-bf16"])
        self.assertIn(">−10.0%</text>", svg)          # adamw: 1000 -> 900
        self.assertIn(">+2.0%</text>", svg)                # read-bf16 from its first release, 500 -> 510
        self.assertEqual(svg.count('class="down"'), 2)     # the key's and adamw's step to 2.0.10
        self.assertEqual(svg.count('class="up"'), 2)       # the key's and read-bf16's step to 2.0.11
        self.assertEqual(svg.count('class="gapband"'), 2)  # the key's and read-bf16 on 2.0.9
        self.assertNotIn('class="cut"', svg)

    def test_a_line_below_the_floor_is_cut(self):
        svg, _ = self.draw([count("v2.0.9", "softmax-ce", 1000), count("v2.0.10", "softmax-ce", 350)])
        self.assertIn('class="cut"', svg)
        self.assertIn(">−65.0%</text>", svg)
        self.assertIn("is cut there", svg)


if __name__ == "__main__":
    unittest.main()
