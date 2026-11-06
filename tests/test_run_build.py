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

from synth import ROOT, copy_tools
from test_run_guard import FAKE_BEND

# the fake Bend, which also logs each build to $FAKE_LOG
LOGGED = FAKE_BEND.replace("out = Path(", "open(__import__('os').environ['FAKE_LOG'], 'a').write('build\\n')\nout = Path(", 1)
NATIVE = '#include <stdio.h>\n#include "../../lib/mb.h"\n#include "../other/native.c"\nint main(void) { puts(MSG); return 0; }\n'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = d = Path(self.tmp.name)
        (d / "scripts").mkdir()
        copy_tools(d)
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

    def run_raw(self, **env):
        self.log.write_text("")
        env = dict(os.environ, **{"BEND_99": str(self.fake), "VERSIONS": "99", "WORKLOADS": "block-step",
                                  "THREADS": "1", "ROUNDS": "0", "OUT": "results/t", "FAKE_LOG": str(self.log), **env})
        return subprocess.run(["bash", str(self.d / "run.sh")], env=env, capture_output=True, text=True, timeout=120)

    def run_sh(self, **env):
        p = self.run_raw(**env)
        self.assertIn("NO RUNS", p.stdout, p.stderr)
        return len(self.log.read_text().split())

    def fake_reporting(self, path, version):
        path = self.d / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(LOGGED.replace("bend 2.0.99", f"bend {version}"))
        path.chmod(0o755)
        return path

    def later(self, path):
        # a source edited after the build: one minute newer than anything built so far
        t = time.time() + 60
        os.utime(self.d / path, (t, t))



class Builds(Fixture):
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



class Versions(Fixture):
    """Each version's compiler is checked to report the release it names before anything is built."""

    def test_a_binary_that_reports_another_version_stops_the_run(self):
        p = self.run_raw(VERSIONS="98", BEND_98=str(self.fake))
        self.assertEqual(p.returncode, 2)
        self.assertIn("reports Bend 2.0.99, not 2.0.98; stopping", p.stderr)
        self.assertEqual(self.log.read_text(), "")

    def test_an_unknown_version_stops_the_run(self):
        p = self.run_raw(VERSIONS="77")
        self.assertEqual(p.returncode, 2)
        self.assertIn("unknown Bend version 77", p.stderr)

    def test_a_version_after_2_0_is_named_in_full(self):
        fake = self.fake_reporting("fake-2.1", "2.1.0")
        self.assertEqual(self.run_sh(VERSIONS="2.1.0", BEND_2_1_0=str(fake)), 1)
        builds = (self.d / "results" / "t" / "builds.tsv").read_text().splitlines()[1:]
        self.assertEqual([b.split("\t")[:3] for b in builds], [["block-step", "2.1.0", "ok"]])
        self.assertTrue((self.d / "build" / "2.1.0" / "block-step").exists())
        self.assertIn("bend_2.1.0\tbend 2.1.0", (self.d / "results" / "t" / "env.tsv").read_text())

    def test_env_tsv_records_the_machine_and_the_sources(self):
        self.run_sh()
        env = dict(l.split("\t", 1) for l in (self.d / "results" / "t" / "env.tsv").read_text().splitlines()[1:])
        for k in ("governor", "no_turbo", "thp", "bun", "pre_loadavg", "pre_other_processes", "pre_cpu3_sibling",
                  "busy"):
            self.assertIn(k, env)
        self.assertRegex(env["source_99"], r"^binary sha256:[0-9a-f]{16}$")
        # a source build's wrapper names its tree, whose commit is the source
        tree = self.d / "src"
        (tree / "bend2").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(tree)], check=True)
        subprocess.run(["git", "-C", str(tree), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                        "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        head = subprocess.run(["git", "-C", str(tree), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        (self.d / "build" / "bin").mkdir(parents=True, exist_ok=True)
        wrapper = self.d / "build" / "bin" / "99"
        wrapper.write_text(f'#!/bin/sh\n[ "$1" = version ] && {{ echo bend 2.0.99; exit 0; }}\nexec bun {tree}/bend2/main.ts "$@"\n')
        wrapper.chmod(0o755)
        self.run_raw()
        env = dict(l.split("\t", 1) for l in (self.d / "results" / "t" / "env.tsv").read_text().splitlines()[1:])
        self.assertEqual(env["source_99"], f"source {head} ({tree})")

    def test_39_is_its_fixed_copy_not_the_installed_pin(self):
        # ~/.bend/bin/bend moves to the next pin with setup.sh; ~/.bend-2.0.39 stays 2.0.39
        self.fake_reporting("home/.bend/bin/bend", "2.0.40")
        self.fake_reporting("home/.bend-2.0.39/bin/bend", "2.0.39")
        env = dict(VERSIONS="39", HOME=str(self.d / "home"))
        self.assertEqual(self.run_sh(**env), 1)
        self.assertIn("bend_39\tbend 2.0.39", (self.d / "results" / "t" / "env.tsv").read_text())
        (self.d / "home" / ".bend-2.0.39" / "bin" / "bend").write_text(LOGGED.replace("2.0.99", "2.0.40"))
        p = self.run_raw(**env)
        self.assertEqual(p.returncode, 2)
        self.assertIn("reports Bend 2.0.40, not 2.0.39; stopping", p.stderr)


if __name__ == "__main__":
    unittest.main()
