# Plan v1: a corpus to run on every release (2026-10-25)

**Done the same day** (NOTES.md): every workload gives the same bytes at 1 and 16 threads (`results/2026-10-25-e/`);
`release.sh` found 2.0.39's change on its own in 2m13s (`results/2026-10-25-2.0.39/`); five new workloads and three
more C targets (`results/2026-10-25-f/`); the law t8_is_dotr, proved with `--verdict`, four mutants rejected
(`laws/`). Not met as written: the law is about a model of the loops, not the `Array` code, and the only mutant the
numeric tests miss is a harmless one.

Plan v0 showed the corpus sees changes the runtime benches miss. v1 makes it something to run on every release: every workload on one and many threads, more of the ML work that bend-ml, llama.bend and BendTorch do, one
command per Bend release, and the first law tying a fast kernel to its spec. Publishing is decided after v1. In order:

## 1. Threads

Every workload also at 16 threads (unpinned, `+RTS --threads 16 -RTS`, bare before 2.0.38), 5 rounds. Per version:
the speedup over one thread, and the output's hash at 1 and 16 (Bend's promise: the same bits at any thread count).
Wall time is the measure here (counters sum over threads); the thread guard checks 16 is honored.
Pass: a table of speedups by version, every hash equal across thread counts, or the difference recorded.

## 2. A run per release

`release.sh <version>`: installs a new Bend side by side (the release's `install.sh` into `~/.bend-<v>`), builds the
corpus with it, runs it next to the previous release, and writes `results/<date>-<v>/` with what moved beyond noise
and any output that changed. The command to run when a release lands.
Pass: it runs end to end on the current release against the one before (2.0.39 against 2.0.38).

## 3. More workloads

- `attention`: BendTorch's attention layer forward and backward at SmolLM2-135M's sizes (the row-wise, F32 work that
  is not a product).
- `rmsnorm` and `adamw`: a row-wise normalization and the optimizer's update over a large parameter array (the
  element-wise loops of every training step).
- `dense-read`: weights read from a file, native `File.read` against `bend-ml-binary-read` (the language limit Taelin
  called a bug), with the bytes hashed.
- C targets for `mnist-step` and the new element-wise workloads, the same bits.
Pass: each new workload builds on 2.0.35-2.0.39 or records why not, prints the same hash everywhere, and joins
`run.sh`.

## 4. A law (phase 2)

Experiment 3 of the analysis: the Tile8 product proved equal to the scalar dot it reorders, stated over a parametric
arithmetic and checked at `Nat` (F32 is opaque to the checker), without changing the kernel's speed. A mutant of the
fast loop that the tests miss must break the proof.
Pass: proved in about 3 days with no `@unsafe` and no axiom, `gemm-tile8`'s counts unchanged; otherwise recorded as
not reachable yet, with why.

## Out

GPU beyond measuring, cluster work, new production kernels (the softmax over arrays belongs to bend-ml), patches to
the compiler.

## Toward the v1.0.0 release (2026-10-27)

**Done on 2026-10-27** (NOTES.md): the tool checks itself. `oracles.tsv` and `make check` (every workload on 1 and 16
threads and every C target against its hash), `make test` (analyze.py, chart.py and run.sh's thread guard on synthetic
runs), `make mutate` (52 mutants, 46 caught, 6 expected to survive, each with its reason), and CI running all of it
with `make laws` on every push. Every workload has a C target with the same bits (five new; gemm-fork and read-binary
reuse their twin's). Six laws instead of one, 16 mutants refused, two of them about the packages' real code
(`bands_len`, `matvec_l_len`, `t8_rows_split`). Left: the parallel run of tensor-fork's blocks over shared arrays, and
its split by columns, are not proved (Base has no fact that writes to different indexes commute).

Next, in order:

1. **A stronger oracle for the whole-block workloads.** `block-step`, `attention-step` and `rmsnorm-step` print only
   each step's loss, so one rounding changed in a layer can pass (the SiLU mutants). Hash the final weights as well,
   then rerun every version to rebuild `oracles.tsv` (bits only, no idle machine needed).
   Pass: the SiLU rounding mutants are caught, and the old and new hashes are both recorded.
2. **The five new C targets, measured.** An idle run of 2.0.39 with the eleven targets: the Bend / C ratios of
   rmsnorm-step, attention-step and block-step, and why gemm-fork came out under 1.0x against its C in a busy smoke
   (0.94x in cycles, where gemm-tile8 is 1.33x).
3. **A GPU lane** (topic 4). Two or three workloads through tensor-gpu and BendTorch's gpu lane, timed by the kernel
   and checked by the same bits, so the corpus follows the compiler's CUDA output too.
   Pass: the same hash on the GPU as on the CPU, or the difference recorded, and a kernel time per version.
4. **A longer history** (topic 5). Run the corpus on 2.0.30-2.0.34, where the workloads build, on the idle machine at
   night; a workload that does not build on a version is recorded, not patched.
   Pass: a series from the oldest version that builds to 2.0.39, in `results/`.
5. **A stable format** (topic 6). `docs/format.md` (what a workload is, `runs.tsv` and `env.tsv`, how a workload and its
   oracle are added), a VERSIONING like the other projects', and the tag `v1.0.0` on `main` through a release PR.
   Small: drop CI's `v1/**` push trigger, and decide whether to pin clang.
6. **Launch day** (topic 7). When Bend 2.0.40 ships: `./release.sh 2.0.40` on the idle machine, its results, the chart
   again, the repository public, then the posts. The checklist is in the launch notes.
