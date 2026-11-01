"""run.sh's builds, on a fake Bend in a copy of the repository: a binary is reused only while it is newer than every
source it was built from (its main.bend, native.c, the files a native.c includes, lib/, the compiler); otherwise it is
built again. A binary left from older sources would be measured as the new one."""
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from synth import ROOT
from test_run_guard import FAKE_BEND

# the fake Bend, which also logs each build to $FAKE_LOG
LOGGED = FAKE_BEND.replace("out = Path(", "open(__import__('os').environ['FAKE_LOG'], 'a').write('build\\n')\nout = Path(", 1)
NATIVE = '#include <stdio.h>\n#include "../../lib/mb.h"\n#include "../other/native.c"\nint main(void) { puts(MSG); return 0; }\n'


class Builds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = d = Path(self.tmp.name)
        (d / "scripts").mkdir()
        for f in ("run.sh", "analyze.py", "scripts/oracle_diff.py"):
            shutil.copy(ROOT / f, d / f)
        (d / "oracles.tsv").write_text("workload\thash\nblock-step\t4355a46b19d348dc\n")
        (d / "workloads" / "block-step").mkdir(parents=True)
        (d / "workloads" / "block-step" / "main.bend").write_text("")
        (d / "workloads" / "other").mkdir()
        (d / "workloads" / "other" / "native.c").write_text('#define MSG "1"\n')
        (d / "lib").mkdir()
        (d / "lib" / "mb.bend").write_text("")
        (d / "lib" / "mb.h").write_text("")
        (d / "data").mkdir()
        (d / "data" / "dense.bin").write_bytes(b"")
        self.fake = d / "fake-bend"
        self.fake.write_text(LOGGED)
        self.fake.chmod(0o755)
        self.log = d / "builds.log"

    def tearDown(self):
        self.tmp.cleanup()

    def run_sh(self, **env):
        self.log.write_text("")
        env = dict(os.environ, BEND_99=str(self.fake), VERSIONS="99", WORKLOADS="block-step", THREADS="1",
                   ROUNDS="0", OUT="results/t", FAKE_LOG=str(self.log), **env)
        p = subprocess.run(["bash", str(self.d / "run.sh")], env=env, capture_output=True, text=True, timeout=120)
        self.assertIn("NO RUNS", p.stdout, p.stderr)
        return len(self.log.read_text().split())

    def later(self, path):
        # a source edited after the build: one minute newer than anything built so far
        t = time.time() + 60
        os.utime(self.d / path, (t, t))

    def test_a_binary_newer_than_its_sources_is_reused(self):
        self.assertEqual(self.run_sh(), 1)
        self.assertEqual(self.run_sh(), 0)
        self.assertEqual(self.run_sh(REBUILD="1"), 1)

    def test_a_newer_main_bend_builds_it_again(self):
        self.run_sh()
        self.later("workloads/block-step/main.bend")
        self.assertEqual(self.run_sh(), 1)

    def test_a_newer_lib_file_builds_it_again(self):
        self.run_sh()
        self.later("lib/mb.bend")
        self.assertEqual(self.run_sh(), 1)

    def test_a_newer_compiler_builds_it_again(self):
        self.run_sh()
        self.later("fake-bend")
        self.assertEqual(self.run_sh(), 1)

    @unittest.skipUnless(shutil.which("clang"), "needs clang")
    def test_a_c_target_is_built_again_when_a_file_it_includes_is_newer(self):
        (self.d / "workloads" / "block-step" / "native.c").write_text(NATIVE)
        c = self.d / "build" / "c" / "block-step"
        self.run_sh()
        first = c.stat().st_mtime_ns
        self.run_sh()
        self.assertEqual(c.stat().st_mtime_ns, first)
        for src in ("workloads/other/native.c", "lib/mb.h", "workloads/block-step/native.c"):
            time.sleep(0.01)
            self.later(src)
            self.run_sh()
            self.assertGreater(c.stat().st_mtime_ns, first, src)
            first = c.stat().st_mtime_ns


if __name__ == "__main__":
    unittest.main()
