"""scripts/bump_bend.sh in a copy of the files it edits, with a stand-in curl that "downloads" a fixed tarball per
architecture: every pin moves to the new release, run.sh learns its fixed copy and runs it by default, and a second
run says it is already there. Needs git (for its diff --stat)."""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

FILES = ("scripts/bump_bend.sh", "scripts/setup.sh", "scripts/check_oracles.sh", "CLAUDE.md", "Makefile",
         ".github/workflows/ci.yml", "README.md", "run.sh")
# writes "tarball <file name>" to the file after -o
CURL = '#!/bin/sh\nwhile [ "$1" != -o ]; do shift; done\nprintf "tarball %s" "$(basename "$2")" > "$2"\n'


def sha(name):
    return hashlib.sha256(f"tarball {name}".encode()).hexdigest()


@unittest.skipUnless(shutil.which("git"), "needs git")
class BumpBend(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = d = Path(self.tmp.name)
        for f in FILES:
            (d / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / f, d / f)
        (d / "bin").mkdir()
        (d / "bin" / "curl").write_text(CURL)
        (d / "bin" / "curl").chmod(0o755)
        subprocess.run(["git", "init", "-q", str(d)], check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def bump(self, version):
        env = dict(os.environ, PATH=f"{self.d / 'bin'}:{os.environ['PATH']}")
        return subprocess.run(["bash", str(self.d / "scripts" / "bump_bend.sh"), version], env=env,
                              capture_output=True, text=True, timeout=60)

    def read(self, f):
        return (self.d / f).read_text()

    def test_every_pin_moves(self):
        p = self.bump("2.0.40")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        setup = self.read("scripts/setup.sh")
        self.assertIn("BEND_VERSION=2.0.40\n", setup)
        self.assertIn(f"SHA={sha('bend-2.0.40-linux-x64.tar.gz')} ;;", setup)
        self.assertIn(f"SHA={sha('bend-2.0.40-linux-arm64.tar.gz')} ;;", setup)
        self.assertNotIn("2.0.39", setup)
        self.assertIn("\nPIN=2.0.40\n", self.read("scripts/check_oracles.sh"))
        self.assertIn("Bend's working pin is **2.0.40**", self.read("CLAUDE.md"))
        self.assertIn("install the pinned Bend (2.0.40)", self.read("Makefile"))
        self.assertIn("Set up (Bend 2.0.40, Lean", self.read(".github/workflows/ci.yml"))
        readme = self.read("README.md")
        self.assertIn("make setup     # Bend 2.0.40 (checked by SHA256)", readme)
        self.assertIn("Bend 2.0.35-2.0.40, 5 rounds", readme)
        run = self.read("run.sh")
        self.assertIn('    39) echo "$HOME/.bend-2.0.39/bin/bend" ;;\n    40) echo "$HOME/.bend-2.0.40/bin/bend" ;;\n', run)
        self.assertIn('VERSIONS=${VERSIONS:-"35 36 37 38 39 40"}', run)
        self.assertEqual(subprocess.run(["bash", "-n", str(self.d / "run.sh")]).returncode, 0)
        self.assertIn("a fixed copy of 2.0.40 at ~/.bend-2.0.40", p.stdout)
        p = self.bump("2.0.40")
        self.assertEqual((p.returncode, p.stdout), (0, "already on 2.0.40\n"))

    def test_a_release_after_2_0_is_named_in_full(self):
        self.assertEqual(self.bump("2.0.40").returncode, 0)
        p = self.bump("2.1.0")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        run = self.read("run.sh")
        self.assertIn('    2.1.0) echo "$HOME/.bend-2.1.0/bin/bend" ;;\n', run)
        self.assertIn('VERSIONS=${VERSIONS:-"35 36 37 38 39 40 2.1.0"}', run)
        self.assertIn("\nPIN=2.1.0\n", self.read("scripts/check_oracles.sh"))


if __name__ == "__main__":
    unittest.main()
