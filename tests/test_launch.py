"""scripts/launch.sh's order and decisions, in a copy of the repository where every step it calls is a stand-in that
logs its call: a busy preflight stops it unless BUSY_OK=1; the #1781 probe runs only on a release that contains the
probe's commit, with both versions' compilers; a hash that is not its oracle goes on to the chart and the report and
exits 1; release.sh stopping stops it."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT
from test_release import git

STUBS = {
    "scripts/preflight.sh": 'echo "preflight" >> "$LOG"; exit "${FAKE_BUSY:-0}"',
    "release.sh": 'if [ "$1" = --previous ]; then echo "$FAKE_PREVIOUS"; exit 0; fi\n'
                  'echo "release $1 OUT=$OUT GPU=$GPU" >> "$LOG"\n'
                  'mkdir -p "$OUT" build/bin; [ "${FAKE_RELEASE:-0}" -gt 1 ] || : > "$OUT/oracles.txt"\n'
                  '# a source build stays behind for a version that is not an installed release (35-39)\n'
                  'case $1 in 2.0.3?) ;; *) : > "build/bin/${1##*.}"; chmod +x "build/bin/${1##*.}" ;; esac\n'
                  'exit "${FAKE_RELEASE:-0}"',
    "probes/1781/build.sh": 'echo "probe-build $1 $2" >> "$LOG"; echo "/p/$2-a"; echo "/p/c"',
    "probes/1781/count.sh": 'echo "probe-count ROUNDS=$ROUNDS $*" >> "$LOG"; echo binary',
    "probes/1781/summarize.py": None,
    "scripts/chart.py": None,
    "scripts/report.py": None,
}
PY_STUB = 'import os, sys\nopen(os.environ["LOG"], "a").write(" ".join([NAME] + sys.argv[1:]) + "\\n")\nprint("report")\n'


class Launch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = d = Path(self.tmp.name) / "mb"
        (d / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts" / "launch.sh", d / "scripts")
        for path, body in STUBS.items():
            p = d / path
            p.parent.mkdir(parents=True, exist_ok=True)
            if body is None:
                p.write_text(PY_STUB.replace("NAME", repr(Path(path).name)))
            else:
                p.write_text("#!/usr/bin/env bash\n" + body + "\n")
            p.chmod(0o755)
        (d / "Makefile").write_text('check-gpu:\n\techo "check-gpu" >> "$$LOG"\n')
        # a fake bendlang/bend: v2.0.39, then the probe's commit, then v2.0.40
        up = d / "build" / "bend"
        up.mkdir(parents=True)
        git("init", "-q", cwd=up)
        self.probe = {}
        for msg, tag in (("old", "v2.0.39"), ("probe", None), ("new", "v2.0.40")):
            git("commit", "-q", "--allow-empty", "-m", msg, cwd=up)
            if tag:
                git("tag", tag, cwd=up)
            self.probe[msg] = subprocess.run(["git", "-C", str(up), "rev-parse", "HEAD"], capture_output=True,
                                             text=True).stdout.strip()
        self.log = d / "log"

    def tearDown(self):
        self.tmp.cleanup()

    def launch(self, version, **env):
        self.log.write_text("")
        env = dict(os.environ, **{"LOG": str(self.log), "OUT": str(self.d / "scratch" / "run"),
                                  "PROBE_COMMIT": self.probe["probe"], "FAKE_PREVIOUS": "2.0.39", **env})
        p = subprocess.run(["bash", str(self.d / "scripts" / "launch.sh"), version], env=env, capture_output=True,
                           text=True, timeout=60)
        return p, self.log.read_text().splitlines()

    def test_a_busy_machine_stops_it_first(self):
        p, log = self.launch("2.0.40", FAKE_BUSY="1")
        self.assertEqual(p.returncode, 1)
        self.assertIn("stopping on a busy machine", p.stdout)
        self.assertEqual(log, ["preflight"])

    def test_the_steps_in_order_with_the_probe(self):
        p, log = self.launch("2.0.40", FAKE_BUSY="1", BUSY_OK="1")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        out = self.d / "scratch" / "run"
        self.assertEqual(log, [
            "preflight", "check-gpu", f"release 2.0.40 OUT={out} GPU=1",
            f"probe-build {Path.home()}/.bend-2.0.39/bin/bend 39", f"probe-build {self.d}/build/bin/40 40",
            "probe-count ROUNDS=5 /p/39-a /p/c /p/40-a",
            f"summarize.py {out}/probe-1781.tsv",
            f"chart.py 40 {out} {out}/results-2.0.40.svg",
            f"report.py {out}"])
        self.assertEqual((out / "report.md").read_text(), "report\n")

    def test_no_probe_on_a_release_without_its_commit(self):
        p, log = self.launch("2.0.39", FAKE_PREVIOUS="2.0.38")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("does not contain", p.stdout)
        self.assertFalse([l for l in log if l.startswith("probe")])
        self.assertTrue(log[-1].startswith("report.py "))

    def test_a_differing_hash_goes_on_and_fails_it(self):
        p, log = self.launch("2.0.39", FAKE_PREVIOUS="2.0.38", FAKE_RELEASE="1")
        self.assertEqual(p.returncode, 1)
        self.assertIn("some hashes are not their oracles", p.stdout)
        self.assertTrue(log[-1].startswith("report.py "))

    def test_release_stopping_stops_it(self):
        p, log = self.launch("2.0.39", FAKE_PREVIOUS="2.0.38", FAKE_RELEASE="2")
        self.assertEqual(p.returncode, 2)
        self.assertEqual(log[-1], f"release 2.0.39 OUT={self.d / 'scratch' / 'run'} GPU=1")

    def test_under_results_the_chart_goes_to_docs(self):
        p, log = self.launch("2.0.39", FAKE_PREVIOUS="2.0.38", OUT="results/x")
        self.assertIn("chart.py 39 results/x docs/results-2.0.39.svg", log)


if __name__ == "__main__":
    unittest.main()
