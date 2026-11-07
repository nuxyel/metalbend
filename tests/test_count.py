"""scripts/count.sh with a fake Bend and a fake valgrind: the row it prints (Ir, D1 misses as reads plus writes,
last-level misses as instructions plus data), the hash against oracles.tsv, a failed build, the runtime's thread
option before and after 2.0.38, and a workload built once and again only when a source is newer."""
import hashlib
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from synth import ROOT

FAKE_BEND = """#!/bin/sh
if [ "$1" = version ]; then echo "bend ${FAKE_VERSION:-2.0.40}"; exit 0; fi
echo built >> "$FAKE_DIR/builds"
case $PWD in */broken) echo "a type error" >&2; exit 1 ;; esac
printf '#!/bin/sh\\necho "$@" > %s/args\\necho hello\\n' "$FAKE_DIR" > "$3"
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


class Count(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.d = Path(self.tmp.name)
        self.mb = mb = d / "mb"
        (mb / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts" / "count.sh", mb / "scripts")
        for w in ("hello", "broken"):
            (mb / "workloads" / w).mkdir(parents=True)
            (mb / "workloads" / w / "main.bend").write_text("def main() -> U32:\n  0\n")
        (mb / "lib").mkdir()
        (mb / "lib" / "mb.bend").write_text("# lib\n")
        (mb / "data").mkdir()
        (mb / "data" / "dense.bin").write_bytes(b"\0")
        self.oracles(HELLO)
        (d / "bin").mkdir()
        for name, text in (("bend", FAKE_BEND), ("valgrind", FAKE_VALGRIND)):
            (d / "bin" / name).write_text(text)
            (d / "bin" / name).chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def oracles(self, hello):
        (self.mb / "oracles.tsv").write_text(f"workload\thash\nhello\t{hello}\nbroken\t{'b' * 16}\n")

    def count(self, w="hello", **env):
        e = dict(os.environ, PATH=f"{self.d / 'bin'}:{os.environ['PATH']}", FAKE_DIR=str(self.d), **env)
        return subprocess.run(["bash", str(self.mb / "scripts" / "count.sh"), str(self.d / "bin" / "bend"), w],
                              capture_output=True, text=True, timeout=60, env=e)

    def fields(self, p):
        return dict(zip(["ref", "commit", "version", "workload", "ir", "d1_misses", "ll_misses", "hash", "bits",
                         "clang", "valgrind"], p.stdout.strip().split("\t")))

    def test_a_count_and_its_oracle(self):
        p = self.count()
        self.assertEqual(p.returncode, 0, p.stderr)
        f = self.fields(p)
        self.assertEqual((f["version"], f["workload"], f["ir"], f["d1_misses"], f["ll_misses"]),
                         ("2.0.40", "hello", "1000", "100", "14"))
        self.assertEqual((f["hash"], f["bits"], f["valgrind"]), (HELLO, "ok", "3.22.0"))
        self.assertTrue(f["commit"].startswith("sha256:"))
        self.assertEqual((self.d / "args").read_text(), "+RTS --threads 1 -RTS\n")

    def test_the_header(self):
        p = self.count(HEADER="1")
        self.assertEqual(p.stdout.splitlines()[0].split("\t")[:5], ["ref", "commit", "version", "workload", "ir"])

    def test_before_2_0_38_the_option_is_bare(self):
        p = self.count(FAKE_VERSION="2.0.37")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual((self.d / "args").read_text(), "--threads 1\n")

    def test_another_hash_is_diff(self):
        self.oracles("c" * 16)
        p = self.count()
        self.assertEqual(p.returncode, 1)
        self.assertEqual(self.fields(p)["bits"], "DIFF")

    def test_a_failed_build(self):
        p = self.count("broken")
        self.assertEqual(p.returncode, 3)
        f = self.fields(p)
        self.assertEqual((f["ir"], f["bits"]), ("-", "compile-failed"))

    def test_an_unknown_workload(self):
        self.assertEqual(self.count("nothing").returncode, 2)

    def test_built_once_then_again_when_a_source_is_newer(self):
        self.count()
        self.count()
        self.assertEqual((self.d / "builds").read_text().count("built"), 1)
        time.sleep(0.01)
        later = time.time() + 5
        os.utime(self.mb / "lib" / "mb.bend", (later, later))
        self.count()
        self.assertEqual((self.d / "builds").read_text().count("built"), 2)


if __name__ == "__main__":
    unittest.main()
