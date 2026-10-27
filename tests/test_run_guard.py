"""run.sh's thread guard, on a fake Bend in a copy of the repository: a version that runs another thread count than it
was asked for stops the run before anything is measured; one that honors it passes."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

# a stand-in for `bend`: `version` prints one, `main.bend -o <out>` writes <out>, a program that starts FAKE_THREADS
# threads in all (or the count after +RTS --threads) and holds them long enough for the guard to count them
FAKE_BEND = """#!/usr/bin/env python3
import sys
from pathlib import Path
if sys.argv[1:] == ["version"]:
    print("bend 2.0.99")
    sys.exit(0)
out = Path(sys.argv[sys.argv.index("-o") + 1])
out.write_text('''#!/usr/bin/env python3
import os, sys, threading, time
a = sys.argv[1:]
n = int(os.environ.get("FAKE_THREADS") or a[a.index("--threads") + 1])
for _ in range(n - 1):
    threading.Thread(target=time.sleep, args=(0.4,)).start()
time.sleep(0.4)
print(1)
''')
out.chmod(0o755)
"""


class Guard(unittest.TestCase):
    def run_sh(self, threads, fake_threads=""):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for f in ("run.sh", "analyze.py"):
                shutil.copy(ROOT / f, d / f)
            (d / "workloads" / "block-step").mkdir(parents=True)
            (d / "workloads" / "block-step" / "main.bend").write_text("")
            (d / "data").mkdir()
            (d / "data" / "dense.bin").write_bytes(b"")
            fake = d / "fake-bend"
            fake.write_text(FAKE_BEND)
            fake.chmod(0o755)
            env = dict(os.environ, BEND_99=str(fake), VERSIONS="99", WORKLOADS="block-step", THREADS=threads,
                       ROUNDS="0", OUT="results/t", FAKE_THREADS=fake_threads)
            p = subprocess.run(["bash", str(d / "run.sh")], env=env, capture_output=True, text=True, timeout=120)
            peaks = (d / "results" / "t" / "threads.tsv").read_text().splitlines()[1:]
            return p, peaks

    def test_a_version_that_ignores_the_thread_option_stops_the_run(self):
        p, peaks = self.run_sh("1", fake_threads="4")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Bend 2.0.99 ran on 4 threads with the option for 1; stopping", p.stderr)
        self.assertEqual(peaks, ["99\t1\t4"])

    def test_too_few_threads_stop_it_too(self):
        p, peaks = self.run_sh("1 16", fake_threads="1")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("Bend 2.0.99 ran on 1 threads with the option for 16; stopping", p.stderr)

    def test_a_version_that_honors_it_passes(self):
        p, peaks = self.run_sh("1 16")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(peaks, ["99\t1\t1", "99\t16\t16"])


if __name__ == "__main__":
    unittest.main()
