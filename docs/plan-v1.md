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

Next. A longer history (2.0.30-2.0.34) is dropped (Renan, 2026-10-27): what matters is every release from here on.
The rest splits by what it needs. Everything that is bits, code or docs is done now, on a busy machine; every number
that is a timing waits for one idle run, the day 2.0.40 ships, because `release.sh 2.0.40` runs 2.0.39 in the same
rounds, so that run measures the new C targets and the GPU lane at no extra session.

### Without an idle machine, in order

1. **A stronger oracle for the whole-block workloads.** `block-step`, `attention-step` and `rmsnorm-step` print only
   each step's loss, so one rounding changed in a layer can pass (the SiLU mutants). Hash the final weights (and
   gradients where the workload has them) as well, the same in each `native.c`, then rebuild `oracles.tsv` on every
   version (bits only).
   Pass: the SiLU rounding mutants move from expected survivors to caught; the old and new hashes are both recorded in
   NOTES.
2. **Rehearse launch day, bits only.** `ROUNDS=1 ./release.sh 2.0.39` end to end (build from the tags, run, analyze),
   so a change upstream in how Bend builds (bun, the tag layout) shows up now and not on the day. Its timings are thrown
   away; only the hashes are checked against `oracles.tsv`.
   Pass: it runs to the end and every hash matches; what broke, fixed in `release.sh` with a test in `tests/`.
3. **gemm-fork under its C, read from the code and the instruction counts.** Instructions repeat between rounds even
   on a busy machine (cycles do not), so the Bend / C ratio in instructions for the five new targets, and whether
   gemm-fork's 0.94x is fewer instructions or only fewer cycles, can be read now. Diagnosis only: these counts do not go
   in the README or `results/`.
   Pass: a NOTES entry with the instruction ratios and the cause of 0.94x, or what is left for the idle run.
   **Done 2026-10-27** (NOTES.md): fewer cycles, not fewer instructions (tensor-fork's column blocks keep B in L2;
   the C was the plain order); gemm-fork now has its own blocked C; its cycle ratio waits for the idle run.
4. **A GPU lane, wired and checked** (topic 4). Two or three workloads through tensor-gpu and BendTorch's gpu lane,
   printing the same hashes; `make check-gpu` (local, since CI has no GPU), and `run.sh` taking a GPU target with the
   kernel time. The kernel times themselves come from the launch-day run.
   Pass: the same hash on the GPU as on the CPU, or the difference recorded and explained.
5. **A count law for the products** (optional, if it fits in a day). The matrix product gives r x m numbers, the way
   `bands_len` does for matvec, on tensor-array's real code. The parallel run over shared arrays stays out until Base
   has a fact that writes to different indexes commute.
6. **A stable format** (topic 6). `docs/format.md` (what a workload is, `oracles.tsv`, `runs.tsv` and `env.tsv`, how a
   workload and its oracle are added), a VERSIONING like the other projects', CI's `v1/**` push trigger dropped, and
   clang pinned or its version recorded in `env.tsv`. The release PR and the tag `v1.0.0` wait for launch day, so that
   v1.0.0 carries 2.0.40's results.
7. **The launch drafts brought up to date** (private notes): eleven C targets, six laws, the oracle's limit or its fix,
   with the new numbers left as blanks for the launch-day run.

### On the idle machine, the day Bend 2.0.40 ships

8. **Launch day** (topic 7). `./release.sh 2.0.40` on the idle machine (mains power, `performance` profile, no agents
   running), with the GPU lane: from that one run, 2.0.40 against 2.0.39, the cycle ratios of the five new C targets,
   the GPU kernel times, and the chart again. Then the results folder, NOTES, README, the release PR and `v1.0.0`, the
   repository public, and the posts. The checklist is in the launch notes.
