# Plan v0: does the corpus see anything? (2026-10-25)

**Done the same day** (NOTES.md, `results/2026-10-25-b/` and `-c/`): step 3 met its success criterion (Bend 2.0.39
cut softmax-ce's instructions by 65% and mnist-step's by 27%, the same bits, traced to bendlang/bend#1806, whose own
benches saw no change); step 4 gave three stable Bend/C ratios (1.32x, 1.95x, 4.83x) with their main causes. Changes
from the plan as written: `softmax-attn` became `softmax-ce` (tensor-array's cross entropy; attention runs inside
`block-step`), `tiny-llama-step` became `block-step` (BendTorch's SmolLM2-135M block, which reads no files), and
upstream `main` was 2.0.39 plus a flake rename, so 2.0.35 took its place.

Experiments 1 and 2 of the analysis that chose this project. v0 answers one question
before the corpus grows: do real workloads, timed by counters and checked by bits, catch changes between Bend
releases that noise does not explain? If not, the corpus adds nothing over the runtime's own benchmarks, and it stops
here.

## Step 1: six workloads (2-3 days)

Each one cut from code that already exists, its package versions pinned in the import lines, so between runs only the
Bend version changes. Each prints one hash of its output (the oracle) and runs one thread on CPU 3.

| Workload | From | Why |
|---|---|---|
| `matvec-bands` | llama.bend's banded matrix-vector product, SmolLM2-1.7B's shapes | the decoding kernel; one array lookup per element |
| `gemm-tile8` | tensor-array's product, SmolLM2-135M's three shapes (`nt`, `tn`, `nn`) | the training kernel; the 2026-10-24 probe already exists |
| `gemm-fork` | the same product through tensor-fork's blocks (`par` 8) | the `@unsafe` sharing path |
| `softmax-attn` | BendTorch's attention units on a short sequence | exp, max, division: the F32 path that is not a product |
| `mnist-step` | bend-ml's MNIST step (784-128-10, batch 100) | a small whole program, not a kernel |
| `tiny-llama-step` | BendTorch's tiny Llama training step | a large whole program: where a kernel's speed in a probe can turn into its opposite |

The last two are there because a kernel's speed alone misleads: tensor-array 0.1.15.0's loop was 23% fewer cycles in a
probe and 1.7x slower inside BendTorch's step (bend-ml NOTES, 2026-10-25).

## Step 2: one script, five Bend versions (1 day)

`run.sh`: builds every workload with every Bend version, then runs 5 rounds, each in a fresh seeded order, with
`perf stat -e instructions,cycles` under `taskset -c 3`, on mains power, `performance` profile, idle machine. One line
per run in `results/<date>/runs.tsv`: workload, Bend version, instructions, cycles, seconds, output hash.

Versions: 2.0.36, 2.0.37, 2.0.38, 2.0.39 (installed side by side) and `main` built from
the upstream clone. A workload that does not build on an older version is recorded as such, not patched.

## Step 3: read the result (half a day)

- **Success**: at least one change between versions beyond the noise of its own rounds (instructions move less than
  0.5% between rounds; cycles a few percent), or a hash that changes, traced to an upstream commit. Bend 2.0.38's GPU
  slowdown on the tiny Llama (+2.6%) is a known candidate on the CPU side too.
- **Stop**: everything within noise and every hash equal. Then MetalBend is closed and the work goes back to the
  three projects.

## Step 4, only after a success: the targets in C (2-3 days)

Experiment 2 of the analysis: a handwritten C version of the dot product, the product of matrices and softmax, with
the same order of sums so the bits match; `perf annotate` of both; one build with `-falign-loops=64` to separate a
real cost from clang's code placement. Success: three stable Bend/C ratios, each with a named cause and a minimal case
under 50 lines in `repros/`. If one cause explains all three, that is one upstream issue, not a project.

## Out of v0

Laws tying each fast workload to its spec (phase 2), GPU beyond measuring, new production kernels, patches to the
compiler, a public release. Whether the repository goes public is Renan's call after step 3.
