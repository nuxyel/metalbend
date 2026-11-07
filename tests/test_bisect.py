"""scripts/bisect_report.py on synthetic counts, Cachegrind files and C (which side of a change a commit is on, the
metrics that moved, the counts per function, the C by definition, the bisects a verdict asks for, the issue's part),
and scripts/bisect.sh on a fake bendlang/bend whose commits change a fake workload's counts: it finds the commit of
each change, skips a commit that does not build, and writes the report. The second part needs bun and git."""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT  # noqa: F401 (puts scripts/ on the path)
import bisect_report as br
from test_release import git

HELLO = hashlib.sha256(b"hello\n").hexdigest()[:16]
HEAD = "ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"


def row(ref, commit, ir, d1, bits="ok", hash="a" * 16):
    if bits in ("compile-failed", "run-failed"):
        ir = d1 = hash = "-"
    return f"{ref}\t{commit}\t2.0.40\tw\t{ir}\t{d1}\t7\t{hash}\t{bits}\t18.1.3\t3.22.0"


class Arithmetic(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def counts(self, *rows):
        p = self.d / "counts.tsv"
        p.write_text("\n".join([HEAD, *rows]) + "\n")
        return br.read_counts(p)

    def test_a_commit_is_bad_past_half_the_change(self):
        rows = self.counts(row("v1", "g", 1000, 100), row("v2", "b", 1100, 100), row("x", "c1", 1050, 100),
                           row("x", "c2", 1051, 100), row("x", "c3", 1002, 100), row("x", "c4", 1300, 100))
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c1")[0], "good")   # exactly half way
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c2")[0], "bad")
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c3")[0], "good")   # a small move is not the change
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c4")[0], "bad")    # past the bad end
        self.assertEqual(br.judge(rows, "ir", "g", "b", "b")[0], "bad")
        self.assertEqual(br.judge(rows, "ir", "g", "b", "g")[0], "good")

    def test_an_improvement_bisects_the_same_way(self):
        rows = self.counts(row("v1", "g", 1000, 100), row("v2", "b", 800, 100), row("x", "c", 850, 100))
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c")[0], "bad")

    def test_d1_misses(self):
        rows = self.counts(row("v1", "g", 1000, 100), row("v2", "b", 1000, 200), row("x", "c", 2000, 120))
        self.assertEqual(br.judge(rows, "d1", "g", "b", "c")[0], "good")
        self.assertEqual(br.judge(rows, "ir", "g", "b", "c")[0], "bad")   # ir's bad end is 1000: any move is past

    def test_skips(self):
        rows = self.counts(row("v1", "g", 1000, 100), row("v2", "b", 1100, 100), row("x", "f", 0, 0, "compile-failed"),
                           row("x", "d", 1100, 100, "DIFF", "b" * 16))
        self.assertEqual(br.judge(rows, "ir", "g", "b", "f")[0], "skip")
        self.assertEqual(br.judge(rows, "ir", "g", "b", "d")[0], "skip")
        self.assertEqual(br.judge(rows, "ir", "g", "b", "missing")[0], "skip")

    def test_bits(self):
        rows = self.counts(row("v1", "g", 1000, 100), row("v2", "b", 1000, 100, "DIFF"),
                           row("x", "ok", 900, 100), row("x", "f", 0, 0, "run-failed"))
        self.assertEqual(br.judge(rows, "bits", "g", "b", "ok")[0], "good")
        self.assertEqual(br.judge(rows, "bits", "g", "b", "b")[0], "bad")
        self.assertEqual(br.judge(rows, "bits", "g", "b", "f")[0], "skip")

    def test_metrics_that_moved(self):
        rows = self.counts(row("v1", "g", 1_000_000, 1000), row("v2", "a", 1_001_001, 1000),
                           row("v2", "b", 1_001_000, 1051), row("v2", "c", 900_000, 2000),
                           row("v2", "d", 1_000_000, 1000, "DIFF"), row("v2", "e", 0, 0, "compile-failed"))
        self.assertEqual(br.moved(rows["g"], rows["a"]), ["ir"])
        self.assertEqual(br.moved(rows["g"], rows["b"]), ["d1"])
        self.assertEqual(br.moved(rows["g"], rows["c"]), ["ir", "d1"])
        self.assertEqual(br.moved(rows["g"], rows["d"]), ["bits"])
        self.assertEqual(br.moved(rows["g"], rows["e"]), [])
        self.assertEqual(br.moved(rows["g"], rows["g"]), [])

    def test_cachegrind_per_function(self):
        p = self.d / "w.cachegrind"
        p.write_text("desc: I1 cache: 65536 B, 64 B, 16-way associative\ncmd: ./w\n"
                     "events: Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw\n"
                     "fl=???\nfn=span_fade\n0 100 0 0 10 3 0 5 2\n0 50\n"
                     "fl=/x.h\nfn=(1) WL_FID_main\n0 7 0 0 1 1\nfn=(1)\n0 3 0 0 0 0 0 1 1\n"
                     "fl=/y.h\nfn=span_fade\n0 1 0 0 0 0 0 0 1\nsummary: 161 0 0 11 4 0 6 3 3\n")
        f = br.cg_functions(p)
        self.assertEqual(f["span_fade"], {"ir": 151, "d1": 3 + 2 + 1})
        self.assertEqual(f["WL_FID_main"], {"ir": 10, "d1": 1 + 1})

    def test_functions_compared(self):
        old = {"a": {"ir": 100, "d1": 1}, "b": {"ir": 1000, "d1": 5}, "c": {"ir": 10, "d1": 0}}
        new = {"a": {"ir": 1100, "d1": 1}, "b": {"ir": 990, "d1": 50}, "d": {"ir": 5, "d1": 0}}
        rows, total = br.compare_functions(old, new, "ir")
        self.assertEqual(total, 1000 - 10 - 10 + 5)
        self.assertEqual([r["function"] for r in rows], ["a", "b", "c", "d"])
        self.assertEqual([r["moved"] for r in rows], [True, False, False, False])
        rows, total = br.compare_functions(old, new, "d1")
        self.assertEqual([(r["function"], r["delta"]) for r in rows], [("b", 45)])

    def test_the_c_by_definition(self):
        old = ["#define X 1", "FAR u64 span_fade(Env e, Term t) {", "  return 1;", "}", "",
               "INLINE u64 ctr_take(Env e) {", "  return span_fade(e, 0);", "}", "#if !DEVICE",
               "  WL_CASE(FID_main_c0)", "    Term a = r0;", "  }}", "#endif", "static int x = 3;"]
        new = list(old)
        new[2] = "  return 2;"
        new[10] = "    Term a = r1;"
        new[13] = "static int x = 4;"
        spans = br.c_spans(old)
        self.assertEqual([s[0] for s in spans], ["span_fade", "ctr_take", "WL_FID_main_c0"])
        changes = {c[0]: (c[1], c[2]) for c in br.c_changes(old, new)}
        self.assertEqual(changes, {"span_fade": (1, 1), "WL_FID_main_c0": (1, 1), "(top-level)": (1, 1)})

    def test_plan_from_a_verdict(self):
        p = self.d / "verdict.tsv"
        cols = "workload\tverdict\tir_old\tir_new\tir_change\td1_old\td1_new\td1_change\tll_old\tll_new\tbits_old\t" \
               "bits_new\twhy"
        lines = [cols]
        for w, v, irc, d1c in (("a", "regression", "0.094200", "1.030000"), ("b", "improvement", "-0.03", "0"),
                               ("c", "mixed", "-0.02", "0.10"), ("d", "bits", "-", "-"), ("e", "same", "0", "0"),
                               ("f", "regression", "0.002", "0.0")):
            lines.append(f"{w}\t{v}\t1\t1\t{irc}\t1\t1\t{d1c}\t1\t1\tok\tok\t")
        p.write_text("\n".join(lines) + "\n")
        self.assertEqual(br.plan(p), [{"workload": "a", "metrics": "ir d1"}, {"workload": "c", "metrics": "d1"},
                                      {"workload": "d", "metrics": "bits"}, {"workload": "f", "metrics": "ir"}])

    def test_report_and_issue(self):
        out = self.d / "ir"
        self.counts(row("v1", "g" * 40, 1000, 100), row("v2", "b" * 40, 1300, 100),
                    row("p" * 40, "p" * 40, 1000, 100), row("f" * 40, "f" * 40, 1300, 100))
        cg = self.d / "count"
        for c, n in (("p", 100), ("f", 400)):
            (cg / (c * 12)).mkdir(parents=True)
            (cg / (c * 12) / "w.cachegrind").write_text(
                f"events: Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw\nfn=span_fade\n0 {n}\nfn=main\n0 900\n")
        out.mkdir()
        (out / ("p" * 12 + ".c")).write_text("FAR u64 span_fade(Env e) {\n  return 1;\n}\n")
        (out / ("f" * 12 + ".c")).write_text("FAR u64 span_fade(Env e) {\n  return 4;\n}\n")
        (out / "pr.tsv").write_text("1978\tOn Metal, a take is a call\thttps://github.com/bendlang/bend/pull/1978\n")
        kv = br.write_report(out, "w", "ir", "v1", "v2", self.d / "counts.tsv", "f" * 40, "p" * 40, "a subject",
                             out / "pr.tsv", cg, commits=118)
        self.assertEqual((kv["pr"], kv["step_change"], kv["range_change"]), ("1978", "+30.00%", "+30.00%"))
        self.assertEqual((kv["functions_moved"], kv["c_changed"]), ("span_fade", "span_fade"))
        md = (out / "report.md").read_text()
        self.assertIn("[bendlang/bend#1978](https://github.com/bendlang/bend/pull/1978)", md)
        self.assertIn("| `span_fade` | 100 | 400 | +300 | 100.0% | moved |", md)
        self.assertIn("+  return 4;", md)
        self.assertIn("scripts/bisect.sh w v1 v2 ir", md)
        self.assertTrue((out / "c.diff").read_text().startswith("--- pppppppppppp.c"))
        section = "\n".join(br.issue_section([out / "report.tsv"]))
        self.assertNotIn("/pull/", section)   # no link that would reach bendlang/bend's timeline
        self.assertIn("- **w, instructions**: [`ffffffffffff`](https://github.com/bendlang/bend/commit/" + "f" * 40 +
                      ") (`bendlang/bend#1978`, On Metal, a take is a call), +30.00% at "
                      "that commit, +30.00% over the range; moved most: `span_fade`; its C changed in `span_fade`.",
                      section)


# a fake bendlang/bend: its compiler writes a program whose counts the fake valgrind reads from it
MAIN_TS = """const a = process.argv.slice(2);
if (a[0] === "version") { console.log("bend 2.0.40"); process.exit(0); }
if (BROKEN) { console.error("a type error"); process.exit(1); }
const out = a[a.indexOf("-o") + 1];
if (out.endsWith(".c")) {
  await Bun.write(out, `FAR u64 span_fade(Env e) {\\n  return @IR@;\\n}\\n\\nINLINE u64 ctr_take(Env e) {\\n  return @D1@;\\n}\\n`);
} else {
  await Bun.write(out, "#!/bin/sh\\n# IR=@IR@ D1=@D1@\\necho hello\\n");
  require("fs").chmodSync(out, 0o755);
}
"""
FAKE_VALGRIND = """#!/bin/sh
if [ "$1" = --version ]; then echo valgrind-3.22.0; exit 0; fi
for a; do case $a in --cachegrind-out-file=*) f=${a#*=} ;; esac; done
while [ $# -gt 0 ]; do case $1 in --*) shift ;; *) break ;; esac; done
ir=$(sed -n 's/^# IR=\\([0-9]*\\) D1=.*/\\1/p' "$1"); d1=$(sed -n 's/^# IR=.* D1=\\([0-9]*\\)$/\\1/p' "$1")
printf 'events: Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw\\nfn=main\\n0 1000 0 0 0 0 0 0 0\\nfn=span_fade\\n0 %s 0 0 0 %s 0 0 0 0\\n' \\
  $((ir - 1000)) "$d1" > "$f"
printf 'summary: %s 0 0 0 %s 0 0 0 0\\n' "$ir" "$d1" >> "$f"
exec "$@"
"""
# the commits: (Ir, D1 misses, builds); v2.0.39 is the first, v2.0.40 the last
HISTORY = [(2000, 100, True)] * 5 + [(2000, 100, False)] + [(2000, 100, True)] * 2 + [(2600, 100, True)] * 2 + \
    [(2580, 300, True)] * 2
BROKEN, IR_CHANGE, D1_CHANGE = 5, 8, 10


@unittest.skipUnless(shutil.which("bun") and shutil.which("git"), "needs bun and git")
class Bisect(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        up = d / "upstream"
        (up / "bend2" / "pack").mkdir(parents=True)
        (up / "bend2" / "pack" / "package.json").write_text('{"name": "fake", "version": "0.0.0"}\n')
        git("init", "-q", "-b", "main", cwd=up)
        self.commits = []
        for i, (ir, d1, builds) in enumerate(HISTORY):
            (up / "bend2" / "main.ts").write_text(
                MAIN_TS.replace("BROKEN", "false" if builds else "true").replace("@IR@", str(ir)).replace("@D1@", str(d1)))
            git("add", "-A", cwd=up)
            git("commit", "-q", "--allow-empty", "-m", f"commit {i}", cwd=up)
            self.commits.append(subprocess.run(["git", "-C", str(up), "rev-parse", "HEAD"], capture_output=True,
                                               text=True).stdout.strip())
        git("tag", "v2.0.39", self.commits[0], cwd=up)
        git("tag", "v2.0.40", self.commits[-1], cwd=up)
        self.mb = mb = d / "mb"
        (mb / "scripts").mkdir(parents=True)
        for f in ("bisect.sh", "bisect_report.py", "track_verdict.py", "count.sh", "bend_main.sh"):
            shutil.copy(ROOT / "scripts" / f, mb / "scripts")
        (mb / "workloads" / "w").mkdir(parents=True)
        (mb / "workloads" / "w" / "main.bend").write_text("def main() -> U32:\n  0\n")
        (mb / "lib").mkdir()
        (mb / "lib" / "mb.bend").write_text("# lib\n")
        (mb / "data").mkdir()
        (mb / "data" / "dense.bin").write_bytes(b"\0")
        (mb / "oracles.tsv").write_text(f"workload\thash\nw\t{HELLO}\n")
        subprocess.run(["git", "clone", "-q", str(up), str(mb / "build" / "bend")], check=True, capture_output=True)
        (d / "bin").mkdir()
        (d / "bin" / "valgrind").write_text(FAKE_VALGRIND)
        (d / "bin" / "valgrind").chmod(0o755)
        self.path = f"{d / 'bin'}:{os.environ['PATH']}"

    def tearDown(self):
        self.tmp.cleanup()

    def bisect(self, *metrics):
        return subprocess.run(["bash", str(self.mb / "scripts" / "bisect.sh"), "w", "v2.0.39", "v2.0.40", *metrics],
                              capture_output=True, text=True, timeout=600,
                              env=dict(os.environ, PATH=self.path, PR_LOOKUP="0", OUT=str(self.mb / "out")))

    def report(self, metric):
        return br.read_tsv_kv(self.mb / "out" / metric / "report.tsv")

    def test_each_change_found_and_reported(self):
        p = self.bisect()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("bisecting ir d1", p.stdout)
        ir, d1 = self.report("ir"), self.report("d1")
        self.assertEqual(ir["first_bad"], self.commits[IR_CHANGE])
        self.assertEqual(ir["parent"], self.commits[IR_CHANGE - 1])
        self.assertEqual((ir["step_change"], ir["range_change"]), ("+30.00%", "+29.00%"))
        self.assertEqual(ir["functions_moved"], "span_fade")
        self.assertEqual(ir["c_changed"], "span_fade")
        self.assertEqual(d1["first_bad"], self.commits[D1_CHANGE])
        self.assertEqual(d1["step_change"], "3.00x")
        self.assertEqual(d1["c_changed"], "ctr_take span_fade")
        md = (self.mb / "out" / "ir" / "report.md").read_text()
        self.assertIn("| `span_fade` | 1,000 | 1,600 | +600 | 100.0% | moved |", md)
        # every count taken once, shared by the two bisects
        commits = [line.split("\t")[1] for line in (self.mb / "out" / "counts.tsv").read_text().splitlines()[1:]]
        self.assertEqual(len(commits), len(set(commits)))

    def test_a_commit_that_does_not_build_is_skipped(self):
        p = self.bisect("ir")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        steps = dict(line.split("\t")[:2] for line in
                     (self.mb / "out" / "ir" / "steps.tsv").read_text().splitlines()[1:])
        self.assertEqual(steps[self.commits[BROKEN]], "skip")   # the first commit git tries
        self.assertEqual(self.report("ir")["first_bad"], self.commits[IR_CHANGE])

    def test_nothing_moved(self):
        p = subprocess.run(["bash", str(self.mb / "scripts" / "bisect.sh"), "w", "v2.0.39", self.commits[1]],
                           capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, PATH=self.path, PR_LOOKUP="0", OUT=str(self.mb / "out")))
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
        self.assertIn("nothing moved", p.stdout)


if __name__ == "__main__":
    unittest.main()
