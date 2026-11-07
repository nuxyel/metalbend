"""scripts/track.sh's release lookups on a fake bendlang/bend: releases in version order (2.0.9 before 2.0.10), other
tags left out, --next after the last release giving nothing."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT


@unittest.skipUnless(shutil.which("git"), "needs git")
class Releases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        up = self.up = Path(self.tmp.name) / "upstream"
        up.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=up, check=True, capture_output=True)
        run("init", "-q", "-b", "main")
        run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "one")
        for t in ("v2.0.8", "v2.0.9", "v2.0.10", "v2.0.11-rc1", "nightly", "v2.0.11"):
            run("tag", t)

    def tearDown(self):
        self.tmp.cleanup()

    def track(self, *args):
        p = subprocess.run(["bash", str(ROOT / "scripts" / "track.sh"), *args], capture_output=True, text=True,
                           timeout=60, env=dict(os.environ, BEND_REMOTE=str(self.up)))
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.strip()

    def test_next(self):
        self.assertEqual(self.track("--next", "v2.0.9"), "v2.0.9 v2.0.10")
        self.assertEqual(self.track("--next", "v2.0.10"), "v2.0.10 v2.0.11")
        self.assertEqual(self.track("--next", "v2.0.11"), "")

    def test_previous(self):
        self.assertEqual(self.track("--previous", "v2.0.10"), "v2.0.9")
        self.assertEqual(self.track("--previous", "v2.0.8"), "")


if __name__ == "__main__":
    unittest.main()
