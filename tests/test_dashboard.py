"""scripts/dashboard.py: the release runs' numbers are report.py's, and the site drawn from a synthetic data branch shows
its history (a band where a workload does not build, a triangle where a count moved), the release watch, the bisect
with its pull request and my issue, a page for every workload, and nothing from the machine's paths."""
import re
import tempfile
import unittest
from pathlib import Path

from synth import ROOT
import report
import dashboard

RUN = ROOT / "results" / "2026-11-06-2.0.40"
HEAD = "ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"


def count(rel, w, ir, d1=100, bits="ok"):
    ir, d1 = ("-", "-") if bits != "ok" else (ir, d1)
    return f"{rel}\t{'1' * 40}\t{rel[1:]}\t{w}\t{ir}\t{d1}\t10\t{'a' * 16}\t{bits}\t18.1.3\t3.22.0"


def tsv(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def data_branch(d):
    h = d / "history" / "2026-11-07-v2.0.38-v2.0.40"
    tsv(d / "history" / "index.tsv", ["folder\tfrom\tto\tworkloads\treleases\tcounts\tgaps\trun",
                                      f"{h.name}\tv2.0.38\tv2.0.40\t2\t3\t5\t1\thttps://example.invalid/run"])
    tsv(h / "counts.tsv", [HEAD, count("v2.0.38", "adamw", 1000), count("v2.0.39", "adamw", 1000),
                           count("v2.0.40", "adamw", 900),
                           count("v2.0.38", "read-bf16", 0, bits="compile-failed"),
                           count("v2.0.39", "read-bf16", 500), count("v2.0.40", "read-bf16", 500)])
    tsv(h / "gaps.tsv", ["release\tworkload\tbits\twhy", "v2.0.38\tread-bf16\tcompile-failed\tread-bf16.c: an error"])
    tsv(h / "steps.tsv", ["old\tnew\tworkload\tverdict\tir_old\tir_new\tir_change\td1_old\td1_new\td1_change\twhy",
                          "v2.0.39\tv2.0.40\tadamw\timprovement\t1000\t900\t-0.100000\t100\t100\t0.000000\t"])
    tsv(h / "env" / "adamw.tsv", ["key\tvalue", "date\t2026-11-07T14:31:10+00:00", "clang\tclang version 18"])
    t = d / "track"
    tsv(t / "last-tag", ["v2.0.40"])
    tsv(t / "index.tsv", ["folder\told\tnew\told_commit\tnew_commit\ttrigger\tfindings\tfor_issue\trun",
                          f"2026-11-07-v2.0.39-v2.0.40\tv2.0.39\tv2.0.40\t{'1' * 40}\t{'2' * 40}\tdaily\t1\t1\t"
                          "https://example.invalid/run/1"])
    cols = "workload\tverdict\tir_old\tir_new\tir_change\td1_old\td1_new\td1_change\tll_old\tll_new\tbits_old\tbits_new\twhy"
    tsv(t / "runs" / "2026-11-07-v2.0.39-v2.0.40" / "verdict.tsv",
        [cols, "adamw\tregression\t1000\t1100\t0.100000\t100\t100\t0.000000\t1\t1\tok\tok\tinstructions +10.00%"])
    tsv(t / "runs" / "2026-11-07-v2.0.39-v2.0.40" / "env.tsv", ["key\tvalue", "date\t2026-11-07T15:30:05+00:00"])
    tsv(t / "regressions" / "v2.0.40-bpe-encode-d1" / "report.tsv",
        ["key\tvalue", "workload\tbpe-encode", "metric\td1", "good\tv2.0.39", "bad\tv2.0.40",
         f"first_bad\t{'3c1f0d3a' * 5}", "decided\tyes", "pr\t2036", "pr_title\ta wide def's boxed record",
         "pr_url\thttps://github.com/bendlang/bend/pull/2036", "step_change\t2.03x", "range_change\t2.03x",
         "functions_moved\tWL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go rfc_wrap", "commits\t118"])


class Site(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        data_branch(d / "data")
        dashboard.build(d / "data", d / "site")
        cls.site = d / "site"
        cls.index = (d / "site" / "index.html").read_text()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_the_bend_c_numbers_are_report_pys(self):
        text = report.report(RUN)
        part = text.split("## Bend / C", 1)[1].split("\n## ", 1)[0]
        theirs = {r[0]: float(r[3].rstrip("x")) for r in
                  ([c.strip() for c in l.strip("|").split("|")] for l in part.splitlines() if l.startswith("| "))
                  if r[0] != "workload" and not r[0].startswith("---")}
        _, cells, versions = dashboard.real_counts(ROOT / "results")
        self.assertEqual(versions[-1], "2.0.40")
        self.assertEqual(len(theirs), 15)
        for w, x in theirs.items():
            self.assertEqual(round(cells[(w, "2.0.40")]["c_cyc"], 2), x, w)
            self.assertEqual(cells[(w, "2.0.40")]["run"], RUN.name)

    def test_the_bend_c_chart(self):
        row = re.search(r'href="w/adamw.html">.*?<div class="val">([^<]*)</div>', self.index).group(1)
        self.assertEqual(row, "1.13x")
        self.assertIn("results/2026-10-25-2.0.39", self.index)   # where 2.0.38 comes from
        self.assertIn("idle by the preflight", self.index)

    def test_the_history(self):
        self.assertIn("5 counts; every output was its oracle; 1 release where a workload does not build", self.index)
        self.assertEqual(self.index.count('class="s-down"'), 1)    # adamw's step to 2.0.40, beyond 0.1%
        self.assertEqual(self.index.count('class="s-up"'), 0)
        self.assertEqual(self.index.count('class="s-gap"'), 1)     # read-bf16 on 2.0.38
        self.assertIn("not counted on 2.0.38", self.index)

    def test_the_release_watch_and_the_bisect(self):
        self.assertIn("1 regression", self.index)
        self.assertIn('<code>v2.0.40</code> now', self.index)
        self.assertIn('href="https://github.com/bendlang/bend/pull/2036">bendlang/bend#2036</a>', self.index)
        self.assertIn('href="https://github.com/bendlang/bend/issues/2082">bendlang/bend#2082</a>', self.index)
        self.assertIn("<code>main_bump_go</code>", self.index)

    def test_a_page_for_every_workload(self):
        names = sorted(p.name for p in (ROOT / "workloads").iterdir() if (p / "main.bend").exists())
        self.assertEqual(sorted(p.stem for p in (self.site / "w").glob("*.html")), names)
        bpe = (self.site / "w" / "bpe-encode.html").read_text()
        self.assertIn("<h3>The C target</h3>", bpe)
        self.assertIn("611x", bpe)

    def test_nothing_from_the_machine(self):
        for p in self.site.rglob("*.html"):
            self.assertNotIn("/home/", p.read_text(), p)
        self.assertTrue((self.site / "style.css").exists())


if __name__ == "__main__":
    unittest.main()
