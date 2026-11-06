"""scripts/bump_bend.sh in a copy of the files it edits, with a stand-in curl that "downloads" a fixed tarball per
architecture: every pin moves to the new release, run.sh learns its fixed copy and runs it by default, and a second
run says it is already there. Needs git (for its diff --stat)."""
import hashlib
import os
import re
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


# the pin as the repository has it now and the release after it, so the test bumps one step past each real bump
PIN = re.search(r"^BEND_VERSION=(\S+)$", (ROOT / "scripts" / "setup.sh").read_text(), re.M).group(1)
NEXT = PIN.rsplit(".", 1)[0] + "." + str(int(PIN.rsplit(".", 1)[1]) + 1)
RUN_VERSIONS = re.search(r'^VERSIONS=\$\{VERSIONS:-"([^"]*)"\}$', (ROOT / "run.sh").read_text(), re.M).group(1)


def name(v):  # run.sh's names: a 2.0.x release by its last number, a later one in full
    return v.rsplit(".", 1)[1] if v.startswith("2.0.") else v


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
        old, new = PIN, NEXT
        p = self.bump(new)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        setup = self.read("scripts/setup.sh")
        self.assertIn(f"BEND_VERSION={new}\n", setup)
        self.assertIn(f"SHA={sha(f'bend-{new}-linux-x64.tar.gz')} ;;", setup)
        self.assertIn(f"SHA={sha(f'bend-{new}-linux-arm64.tar.gz')} ;;", setup)
        self.assertNotIn(old, setup)
        self.assertIn(f"\nPIN={new}\n", self.read("scripts/check_oracles.sh"))
        self.assertIn(f"Bend's working pin is **{new}**", self.read("CLAUDE.md"))
        self.assertIn(f"install the pinned Bend ({new})", self.read("Makefile"))
        self.assertIn(f"Set up (Bend {new}, Lean", self.read(".github/workflows/ci.yml"))
        readme = self.read("README.md")
        self.assertIn(f"make setup     # Bend {new} (checked by SHA256)", readme)
        self.assertIn(f"Bend 2.0.35-{new}, 5 rounds", readme)
        run = self.read("run.sh")
        self.assertIn(f'    {name(old)}) echo "$HOME/.bend-{old}/bin/bend" ;;\n'
                      f'    {name(new)}) echo "$HOME/.bend-{new}/bin/bend" ;;\n', run)
        self.assertIn(f'VERSIONS=${{VERSIONS:-"{RUN_VERSIONS} {name(new)}"}}', run)
        self.assertEqual(subprocess.run(["bash", "-n", str(self.d / "run.sh")]).returncode, 0)
        self.assertIn(f"a fixed copy of {new} at ~/.bend-{new}", p.stdout)
        p = self.bump(new)
        self.assertEqual((p.returncode, p.stdout), (0, f"already on {new}\n"))

    def test_a_release_after_2_0_is_named_in_full(self):
        self.assertEqual(self.bump(NEXT).returncode, 0)
        p = self.bump("2.1.0")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        run = self.read("run.sh")
        self.assertIn('    2.1.0) echo "$HOME/.bend-2.1.0/bin/bend" ;;\n', run)
        self.assertIn(f'VERSIONS=${{VERSIONS:-"{RUN_VERSIONS} {name(NEXT)} 2.1.0"}}', run)
        self.assertIn("\nPIN=2.1.0\n", self.read("scripts/check_oracles.sh"))


if __name__ == "__main__":
    unittest.main()
