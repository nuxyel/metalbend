"""The GPU target, in a copy of the repository with a fake driver and toolkit. scripts/check_oracles.sh (make
check-gpu): with no GPU it skips with the reason and passes, so it never breaks a machine (or CI) without one, and its
oracle lines must match the gpu.bend files, both ways. run.sh: GPU=1 with no GPU stops before anything runs."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT, copy_tools

FAKE_BEND = """#!/bin/sh
[ "$1" = version ] && echo "bend 2.0.39" && exit 0
exit 1
"""


class CheckGpu(unittest.TestCase):
    def check(self, oracles, gpu_files, sees_gpu, script="scripts/check_oracles.sh", **extra):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "scripts").mkdir()
            copy_tools(d, ("scripts/check_oracles.sh", "scripts/cuda.sh"))
            for w in ("w", "v"):
                (d / "workloads" / w).mkdir(parents=True)
                (d / "workloads" / w / "main.bend").write_text("")
            for w in gpu_files:
                (d / "workloads" / w / "gpu.bend").write_text("")
            (d / "oracles.tsv").write_text("workload\thash\n" + "".join(f"{w}\t{h}\n" for w, h in oracles))
            (d / "data").mkdir()
            (d / "data" / "dense.bin").write_bytes(b"")
            # a toolkit with nvrtc.h, and an nvidia-smi that lists a GPU or none
            (d / "cuda" / "include").mkdir(parents=True)
            (d / "cuda" / "include" / "nvrtc.h").write_text("")
            (d / "cuda" / "lib64").mkdir()
            (d / "bin").mkdir()
            smi = d / "bin" / "nvidia-smi"
            smi.write_text("#!/bin/sh\n" + ("echo 'GPU 0: Fake GPU (UUID: GPU-0)'\n" if sees_gpu else "exit 9\n"))
            smi.chmod(0o755)
            bend = d / "bin" / "bend"
            bend.write_text(FAKE_BEND)
            bend.chmod(0o755)
            env = dict(os.environ, PATH=f"{d / 'bin'}:{os.environ['PATH']}", CUDA_HOME=str(d / "cuda"),
                       BEND=str(bend), TARGETS="gpu", THREADS="1", WORKLOADS="w v", OUT="build/t", **extra)
            p = subprocess.run(["bash", str(d / script)], env=env, capture_output=True, text=True, timeout=60)
            # the files a run left (its empty folders aside)
            p.made = sorted(str(f.relative_to(d)) for f in (d / "build").rglob("*") if f.is_file())
            return p

    def test_no_gpu_skips_and_passes(self):
        p = self.check([("w", "a" * 16), ("v", "b" * 16), ("w:gpu", "a" * 16)], ["w"], sees_gpu=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("skip the GPU targets: nvidia-smi sees no GPU", p.stdout)
        self.assertIn("check: nothing else to run", p.stdout)

    def test_a_gpu_oracle_with_no_gpu_bend_fails_even_with_no_gpu(self):
        p = self.check([("w", "a" * 16), ("v", "b" * 16), ("v:gpu", "b" * 16)], [], sees_gpu=False)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("FAIL oracles.tsv names v:gpu, which has no workloads/v/gpu.bend", p.stdout)

    def test_a_gpu_bend_with_no_oracle_fails(self):
        p = self.check([("w", "a" * 16), ("v", "b" * 16)], ["w"], sees_gpu=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("FAIL w: a gpu.bend and no oracle w:gpu (add its line to oracles.tsv)", p.stdout)

    def test_run_sh_with_gpu_and_no_gpu_stops(self):
        p = self.check([("w", "a" * 16), ("v", "b" * 16), ("w:gpu", "a" * 16)], ["w"], sees_gpu=False,
                       script="run.sh", GPU="1", BEND_99=str(Path("/nonexistent")), VERSIONS="99", ROUNDS="0")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("GPU=1, but nvidia-smi sees no GPU; stopping", p.stderr)
        self.assertEqual(p.made, [])


if __name__ == "__main__":
    unittest.main()
