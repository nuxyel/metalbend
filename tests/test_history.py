"""scripts/history.sh with fake Bends and a fake valgrind: one row a release, named by the release, a release where
the workload does not build recorded as a gap with its first error line, and --releases giving a range of tags in
version order."""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

# a Bend of one release: its version, and a build that fails on the releases listed in FAKE_BROKEN
FAKE_BEND = """#!/bin/sh
if [ "$1" = version ]; then echo "bend {v}"; exit 0; fi
case " $FAKE_BROKEN " in *" {v} "*) echo "/tmp/bend-AbC123/w.c:12:3: error: too few arguments" >&2; exit 1 ;; esac
printf '#!/bin/sh\\necho hello\\n' > "$3"
chmod +x "$3"
"""
FAKE_VALGRIND = """#!/bin/sh
if [ "$1" = --version ]; then echo valgrind-3.22.0; exit 0; fi
for a; do case $a in --cachegrind-out-file=*) f=${a#*=} ;; esac; done
while [ $# -gt 0 ]; do case $1 in --*) shift ;; *) break ;; esac; done
printf 'events: Ir I1mr ILmr Dr D1mr DLmr Dw D1mw DLmw\\nsummary: 1000 1 2 300 40 5 200 60 7\\n' > "$f"
exec "$@"
"""
HELLO = hashlib.sha256(b"hello\n").hexdigest()[:16]
RELEASES = ("v2.0.32", "v2.0.33", "v2.0.34")


class History(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.d = Path(self.tmp.name)
        mb = self.mb = d / "mb"
        (mb / "scripts").mkdir(parents=True)
        for f in ("history.sh", "count.sh"):
            shutil.copy(ROOT / "scripts" / f, mb / "scripts")
        (mb / "workloads" / "hello").mkdir(parents=True)
        (mb / "workloads" / "hello" / "main.bend").write_text("def main() -> U32:\n  0\n")
        (mb / "lib").mkdir()
        (mb / "data").mkdir()
        (mb / "data" / "dense.bin").write_bytes(b"\0")
        (mb / "oracles.tsv").write_text(f"workload\thash\nhello\t{HELLO}\n")
        (mb / "build" / "bin").mkdir(parents=True)
        for rel in RELEASES:
            b = mb / "build" / "bin" / f"at-{rel}"
            b.write_text(FAKE_BEND.replace("{v}", rel[1:]))
            b.chmod(0o755)
        (d / "bin").mkdir()
        (d / "bin" / "valgrind").write_text(FAKE_VALGRIND)
        (d / "bin" / "valgrind").chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def history(self, *args, **env):
        e = dict(os.environ, PATH=f"{self.d / 'bin'}:{os.environ['PATH']}", NO_BUILD="1", OUT=str(self.d / "out"),
                 **env)
        return subprocess.run(["bash", str(self.mb / "scripts" / "history.sh"), *args], capture_output=True,
                              text=True, timeout=60, env=e)

    def rows(self, name):
        lines = (self.d / "out" / name).read_text().splitlines()
        head = lines[0].split("\t")
        return [dict(zip(head, line.split("\t"))) for line in lines[1:]]

    def test_one_row_a_release(self):
        p = self.history("hello", *RELEASES)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = self.rows("counts.tsv")
        self.assertEqual([r["ref"] for r in rows], list(RELEASES))
        self.assertEqual([r["version"] for r in rows], ["2.0.32", "2.0.33", "2.0.34"])
        self.assertEqual({(r["ir"], r["bits"]) for r in rows}, {("1000", "ok")})
        self.assertEqual(self.rows("gaps.tsv"), [])
        env = dict(line.split("\t", 1) for line in (self.d / "out" / "env.tsv").read_text().splitlines()[1:])
        self.assertEqual((env["workload"], env["releases"]), ("hello", " ".join(RELEASES)))

    def test_a_release_that_does_not_build_is_a_gap(self):
        p = self.history("hello", *RELEASES, FAKE_BROKEN="2.0.32 2.0.33")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual([r["bits"] for r in self.rows("counts.tsv")], ["compile-failed", "compile-failed", "ok"])
        gaps = self.rows("gaps.tsv")
        self.assertEqual([(g["release"], g["bits"]) for g in gaps],
                         [("v2.0.32", "compile-failed"), ("v2.0.33", "compile-failed")])
        self.assertEqual(gaps[0]["why"], "w.c:12:3: error: too few arguments")

    def test_no_workload(self):
        self.assertEqual(self.history("nothing", "v2.0.32").returncode, 2)


@unittest.skipUnless(shutil.which("git"), "needs git")
class Releases(unittest.TestCase):
    def test_a_range_in_version_order(self):
        with tempfile.TemporaryDirectory() as t:
            up = Path(t)
            run = lambda *a: subprocess.run(["git", *a], cwd=up, check=True, capture_output=True)
            run("init", "-q", "-b", "main")
            run("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "one")
            for tag in ("v2.0.8", "v2.0.9", "v2.0.10", "v2.0.11-rc1", "v2.0.11", "v2.0.12"):
                run("tag", tag)
            p = subprocess.run(["bash", str(ROOT / "scripts" / "history.sh"), "--releases", "v2.0.9", "v2.0.11"],
                               capture_output=True, text=True, timeout=60, env=dict(os.environ, BEND_REMOTE=t))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.split(), ["v2.0.9", "v2.0.10", "v2.0.11"])


if __name__ == "__main__":
    unittest.main()
