"""release.sh on a fake bendlang/bend, with no network: a local git repository whose tags each hold a bend2/main.ts
that bun runs as a fake `bend`, cloned into a copy of MetalBend as build/bend. Checks the release it picks as the
one before, that the source wrappers of installed version numbers are dropped even when run.sh stops, and, where perf
counts instructions, that the hashes are compared with oracles.tsv at the end. Needs git and bun (skipped otherwise)."""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

# a fake `bend` for one release: `version` prints it; `main.bend -o <out>` writes a program that prints PRINTS and
# starts the threads it is asked for after --threads (FAKE_THREADS overrides the count), held long enough to be counted
MAIN_TS = """const a = process.argv.slice(2);
if (a[0] === "version") { console.log("bend VERSION"); process.exit(0); }
const out = a[a.indexOf("-o") + 1];
await Bun.write(out, `#!/usr/bin/env python3
import os, sys, threading, time
a = sys.argv[1:]
n = int(os.environ.get("FAKE_THREADS") or a[a.index("--threads") + 1])
for _ in range(n - 1):
    threading.Thread(target=time.sleep, args=(0.3,)).start()
time.sleep(0.3)
print("PRINTS")
`);
require("fs").chmodSync(out, 0o755);
"""
TAGS = ["2.0.9", "2.0.10", "2.0.38", "2.0.39", "2.0.40-rc1", "2.0.40", "2.1.0"]
GOOD = "1"
ORACLE = hashlib.sha256(b"1\n").hexdigest()[:16]


def git(*args, cwd):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
                    "-c", "tag.gpgsign=false", *args], cwd=cwd, check=True, capture_output=True)


def perf_counts():
    try:
        p = subprocess.run(["perf", "stat", "-x,", "-e", "cpu_core/instructions/u", "true"], capture_output=True)
        return p.returncode == 0
    except FileNotFoundError:
        return False


@unittest.skipUnless(shutil.which("bun") and shutil.which("git"), "needs bun and git")
class Release(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        # the fake upstream, one commit per tag
        up = d / "upstream"
        (up / "bend2" / "pack").mkdir(parents=True)
        (up / "bend2" / "pack" / "package.json").write_text('{"name": "fake", "version": "0.0.0"}\n')
        git("init", "-q", cwd=up)
        for v in TAGS:
            prints = "2" if v == "2.0.39" and self.id().endswith("_changed") else GOOD
            (up / "bend2" / "main.ts").write_text(MAIN_TS.replace("VERSION", v).replace("PRINTS", prints))
            git("add", "-A", cwd=up)
            git("commit", "-q", "--allow-empty", "-m", v, cwd=up)
            git("tag", f"v{v}", cwd=up)
        git("tag", "notes", cwd=up)
        # a copy of MetalBend with one workload, its oracle, and the clone of the fake upstream at build/bend
        self.mb = mb = d / "mb"
        (mb / "scripts").mkdir(parents=True)
        for f in ("release.sh", "run.sh", "analyze.py", "scripts/oracle_diff.py"):
            shutil.copy(ROOT / f, mb / f)
        (mb / "workloads" / "block-step").mkdir(parents=True)
        (mb / "workloads" / "block-step" / "main.bend").write_text("")
        (mb / "data").mkdir()
        (mb / "data" / "dense.bin").write_bytes(b"")
        (mb / "oracles.tsv").write_text(f"workload\thash\nblock-step\t{ORACLE}\n")
        git("init", "-q", cwd=mb)
        git("commit", "-q", "--allow-empty", "-m", "copy", cwd=mb)
        subprocess.run(["git", "clone", "-q", str(up), str(mb / "build" / "bend")], check=True, capture_output=True)

    def tearDown(self):
        self.tmp.cleanup()

    def release(self, *args, **env):
        env = dict(os.environ, **{"OUT": "build/rehearsal", "ROUNDS": "1", **env})
        return subprocess.run(["bash", str(self.mb / "release.sh"), *args], env=env, capture_output=True, text=True,
                              timeout=300)

    def test_the_release_before_is_the_last_release_tag(self):
        # numeric order (2.0.10 after 2.0.9), no pre-release, and across a minor version
        for new, old in (("2.0.40", "2.0.39"), ("2.0.10", "2.0.9"), ("2.1.0", "2.0.40")):
            p = self.release("--previous", new)
            self.assertEqual((p.returncode, p.stdout), (0, old + "\n"), p.stderr)

    def test_no_tag_and_no_release_before_stop_it(self):
        p = self.release("--previous", "2.0.41")
        self.assertEqual(p.returncode, 2)
        self.assertIn("no tag v2.0.41", p.stderr)
        p = self.release("--previous", "2.0.9")
        self.assertEqual(p.returncode, 2)
        self.assertIn("no release before 2.0.9", p.stderr)

    def test_the_wrappers_go_even_when_run_sh_stops(self):
        # the fake ignores the thread option, so run.sh's guard stops the run
        p = self.release("2.0.39", ROUNDS="0", FAKE_THREADS="4")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("ran on 4 threads with the option for 1; stopping", p.stderr)
        self.assertFalse((self.mb / "build" / "bin" / "38").exists())
        self.assertFalse((self.mb / "build" / "bin" / "39").exists())

    def test_the_workloads_are_built_by_the_source_builds(self):
        # an installed 2.0.38 or 2.0.39 cannot build the empty main.bend; the fake can. With no rounds, the
        # comparison with oracles.tsv has nothing to read, and says so
        p = self.release("2.0.39", ROUNDS="0")
        builds = (self.mb / "build" / "rehearsal" / "builds.tsv").read_text().splitlines()[1:]
        self.assertEqual([b.split("\t")[:3] for b in builds], [["block-step", "38", "ok"], ["block-step", "39", "ok"]],
                         p.stdout + p.stderr)
        self.assertEqual(p.returncode, 1)
        self.assertIn("NO RUNS", p.stdout)

    def test_a_release_after_2_0_is_named_in_full(self):
        # 2.0.40 is "40" in the run, 2.1.0 is "2.1.0"; neither is an installed release, so their wrappers stay
        p = self.release("2.1.0", ROUNDS="0")
        builds = (self.mb / "build" / "rehearsal" / "builds.tsv").read_text().splitlines()[1:]
        self.assertEqual([b.split("\t")[:3] for b in builds], [["block-step", "40", "ok"], ["block-step", "2.1.0", "ok"]],
                         p.stdout + p.stderr)
        self.assertIn("Bend 2.1.0: bend 2.1.0", p.stdout)
        self.assertTrue((self.mb / "build" / "bin" / "2.1.0").exists())

    def test_old_c_and_gpu_binaries_are_cleared(self):
        # a C or GPU target built before (from an older native.c, say) must not be measured as this release's
        for d in ("c", "gpu-39", "gpu-40"):
            (self.mb / "build" / d).mkdir(parents=True)
            (self.mb / "build" / d / "block-step").write_text("")
        self.release("2.0.39", ROUNDS="0")
        for d in ("c", "gpu-39", "gpu-40"):
            self.assertFalse((self.mb / "build" / d / "block-step").exists(), d)

    def test_a_source_tree_removed_by_hand_is_made_again(self):
        self.release("2.0.39", ROUNDS="0")
        shutil.rmtree(self.mb / "build" / "src")
        p = self.release("2.0.39", ROUNDS="0")
        self.assertIn("Bend 2.0.39: bend 2.0.39", p.stdout, p.stderr)

    @unittest.skipUnless(perf_counts(), "needs perf with the P-core PMU")
    def test_every_hash_its_oracle(self):
        p = self.release("2.0.39")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("Bend 2.0.38: bend 2.0.38", p.stdout)
        self.assertIn("oracles: 4 cases, every hash is its oracle", p.stdout)

    @unittest.skipUnless(perf_counts(), "needs perf with the P-core PMU")
    def test_an_output_changed_from_its_oracle_fails_it_changed(self):
        p = self.release("2.0.39")
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("DIFFERS   block-step, Bend 2.0.39, 1 thread", p.stdout)
        self.assertIn("DIFFERS   block-step, Bend 2.0.39, 16 threads", p.stdout)
        self.assertNotIn("Bend 2.0.38, 1 thread", p.stdout)


if __name__ == "__main__":
    unittest.main()
