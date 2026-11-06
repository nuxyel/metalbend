"""scripts/bend_main.sh on a fake bendlang/bend (as in test_release.py): it builds origin's branch, not a stale local
one, into build/bin/main, and records the commit. Needs git and bun (skipped otherwise)."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT
from test_release import MAIN_TS, git


@unittest.skipUnless(shutil.which("bun") and shutil.which("git"), "needs bun and git")
class BendMain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.up = up = d / "upstream"
        (up / "bend2" / "pack").mkdir(parents=True)
        (up / "bend2" / "pack" / "package.json").write_text('{"name": "fake", "version": "0.0.0"}\n')
        git("init", "-q", "-b", "main", cwd=up)
        self.commit("2.0.39")
        self.mb = d / "mb"
        (self.mb / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts" / "bend_main.sh", self.mb / "scripts")
        subprocess.run(["git", "clone", "-q", str(up), str(self.mb / "build" / "bend")], check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, version):
        (self.up / "bend2" / "main.ts").write_text(MAIN_TS.replace("VERSION", version))
        git("add", "-A", cwd=self.up)
        git("commit", "-q", "-m", version, cwd=self.up)
        return subprocess.run(["git", "-C", str(self.up), "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()

    def bend_main(self, *args):
        return subprocess.run(["bash", str(self.mb / "scripts" / "bend_main.sh"), *args], capture_output=True,
                              text=True, timeout=300, env=dict(os.environ, BEND_NO_TELEMETRY="1"))

    def test_main_is_origins_latest_commit(self):
        head = self.commit("2.0.40-dev")   # upstream moved on after the clone
        p = self.bend_main()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("build/bin/main reports bend 2.0.40-dev", p.stdout)
        self.assertEqual((self.mb / "build" / "bin" / "main.commit").read_text(), head + "\n")
        self.assertIn(f"/build/src/main-{head[:8]}/bend2/main.ts", (self.mb / "build" / "bin" / "main").read_text())

    def test_an_unknown_ref_stops_it(self):
        p = self.bend_main("no-such-branch")
        self.assertEqual(p.returncode, 2)
        self.assertIn("no ref no-such-branch", p.stderr)


if __name__ == "__main__":
    unittest.main()
