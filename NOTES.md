# Notes

What changed, why, and the result in a line, by date. The method and the analysis behind each result live in Renan's
private lab.

## 2026-10-25: plan v0

- Six workloads (`workloads/`), Bend 2.0.35-2.0.39; upstream `main` was 2.0.39 plus a flake rename, so 2.0.35 took its
  place. `softmax-attn` became `softmax-ce` and `tiny-llama-step` became `block-step` (it reads no files).
- `run.sh` counts user mode only: user and kernel together varied ~0.8% between runs (page faults); user mode repeats
  to a few hundred instructions in 13.7 G (`results/2026-10-25-a/`, kept).
- `run.sh` checks that each version really runs one thread: on 2.0.39 a bare `--threads 1` ran 22.
- **Versions** (`results/2026-10-25-b/`): Bend 2.0.39 runs softmax-ce in 64.7% fewer instructions than 2.0.38 and
  mnist-step in 27.1% fewer, the same bits; the other four within 0.03%. All of it is bendlang/bend#1806 (a5bae35c),
  whose own benches saw no change: tensor-array's list walks stopped taking their lists.
- **C targets** (`native.c`, the same bits): Bend 2.0.39 / C in cycles on the quietest run (`results/2026-10-25-d/`,
  the numbers of record) 1.33x gemm-tile8, 2.32x matvec-bands, 4.75x softmax-ce; `-falign-loops=64` moves none by more
  than 3%.
- **Causes.** matvec: each `Array.get` keeps an `and` with the array's mask, which clang cannot drop
  (`repros/dot_mask.bend`, 3.2x instructions; posted on bendlang/bend#1781). gemm: the same mask,
  once per cell of 8, explains a part; the rest is the loop's shape and the runtime's spin. softmax-ce: tensor-array's
  list walks cost 3.4x (`repros/softmax_array.bend`, the same bits over an `Array`), 1.41x left against C.
- Plan v0's go criterion is met; the corpus goes on.

## 2026-10-25: plan v1, step 1, threads

- `run.sh` takes `THREADS`; a run on more threads is unpinned and timed by the wall clock, and the guard checks each
  count (16 asked, 16 seen).
- `results/2026-10-25-e/`: the same bytes at 1 and 16 threads everywhere. At 16 threads: block-step 4.4x, matvec 4.1x,
  gemm-fork 2.2x, mnist-step 1.03x, softmax-ce 1.0x; flat across 2.0.35-2.0.39. The MNIST step and the cross entropy
  barely use the threads: tensor-array's `Mat.softmax_ce` walks its rows one after another, a second lead for bend-ml
  next to the arrays.

## 2026-10-25: plan v1, step 2, a run per release

- `release.sh <version>` builds that release and the one before from their tags with bun (the installer only installs
  the latest), runs the corpus on both at 1 and 16 threads and prints what moved. On 2.0.39 it took 2m13s and found
  the #1806 change by itself (`results/2026-10-25-2.0.39/`).

## 2026-10-25: plan v1, step 3, more workloads

- attention-step and rmsnorm-step (BendTorch's block cut to its attention half and to one RMSNorm), adamw
  (BendTorch's `Opt.mat` on 28.3 M weights), read-native (`File.read_at`, a list cell per byte) and read-binary
  (bend-ml-binary-read) on a 16 MB file from `lib/gen_dense.py`; C targets for adamw, mnist-step and the reads, the
  same bits (`results/2026-10-25-f/`).
- No version moved the new five. Bend/C in cycles: adamw 1.20x, mnist-step 1.96x, read-native 21x (user mode; 6.1x
  wall), read-binary about the C read. read-binary does not build on 2.0.35 (the effect ABI changed in 2.0.36).
- adamw and rmsnorm-step do not use the 16 threads (1.0x): BendTorch's optimizer loop and a 512-row RMSNorm run
  sequentially here.

## 2026-10-25: plan v1, step 4, a law

- `laws/`: t8_is_dotr, Tile8's dot and the scalar dot build the same expression tree (no property of `+` or `*`
  assumed), so they agree under any arithmetic, F32 included. Proved by induction on the cells; `--verdict` checks
  it; four mutants of the model are rejected, one of them harmless in F32 (`s1 + s0`), which shows the law is stricter
  than "the same bits". It speaks about a list model of the loops, not tensor-array's `Array` code; the kernel did
  not change, so its counts did not either.
- The plan's "a mutant the tests miss" is met only by that harmless one: the mutants that change bits change the
  corpus's hashes too.
- Plan v1 done: threads, `release.sh`, eleven workloads with six C targets, a law.

## 2026-10-27: CI and tests of the tool

- `oracles.tsv`: each workload's hash from `results/2026-10-25-f/`, where all five versions on 1 and 16 threads and
  every C target printed it. `make check` builds the eleven workloads with Bend 2.0.39 and the six C targets with
  clang and runs them (1 and 16 threads): 28 runs, every hash its oracle, on my machine (clang 23) and on GitHub's
  ubuntu-24.04 runner (clang 18.1.3, another glibc), so the C targets' bits, `exp` included, did not depend on either.
- `make test`: 25 unit tests of `analyze.py`, `scripts/chart.py` and `run.sh`'s thread guard on synthetic runs.
  The guard's test on the runner found a race: a process ending between two polls made `ls /proc/<pid>/task` fail,
  which ended `run.sh` silently under `pipefail`; fixed.
- `make mutate`: 48 mutants (workloads, C targets, `lib/mb.bend`, `lib/mb.h`, `lib/gen_dense.py`, `oracles.tsv`,
  `analyze.py`, `chart.py`, the guard), 43 caught, 5 survive as expected: the fork depth of `gemm-fork`, a swapped
  addition, a max that takes ties from the right, `calloc`'s swapped arguments (all the same bits) and `>=` for `>` at
  exactly 3x the noise. The first run found one gap, a spread over the mean instead of the median; a test now covers it.
- CI (`.github/workflows/ci.yml`) runs all three on every push in about 3.5 minutes; bits only, no timings.

## 2026-10-27: plan v1, topic 2, a C target for every workload

- `lib/bt.h`: BendTorch 1.1.1's layers in C for the three block workloads (the inputs of smol_block.bend's hash, AdamW
  with Train.step's 1 - b^t recurrence, RMSNorm, MSE with its tree sum, Tile8 products and the precise product's blocks
  of 1024, LinearNB, RoPE, grouped-query attention, SiLU), each loop in the package's order of operations.
- **rmsnorm-step**: the same 200 losses, bit for bit, at the first build. Its dx is computed and dropped, as the layer
  does.
- **attention-step**: the same 4 losses at the first build. The attention sums run over all t positions, the zeros of P
  and G past the diagonal included, as BendTorch's loops do (adding them changes no bit, since no sum starts at -0).
- **block-step**: the same 2 losses at the first build; swapping the order of one product's partial sums changes the
  second loss, so the hash does read the backward pass and the step. The gate and up projections' input gradients
  (k = 1536) go through matmul_precise's two blocks, 1024 then 512.
- **gemm-fork** and **read-binary** take gemm-tile8's and read-native's C unchanged: tensor-fork's blocks run
  tensor-array's own cells (the same bits at every depth), and both reads load the same file.
- Bend's F32 ops gave no surprise: exp, sqrt, pow, cos and sin are libm's double functions rounded to F32 in Bend's C
  (`(f32)exp(x)`), under `fp contract(off)`, and the targets call them the same way. Every hash matches Bend 2.0.39's
  on 1 and 16 threads. No timings: the machine was busy, so the ratios wait for the next idle run.

## 2026-10-27: plan v1 topic 3, more laws

- `laws/` has six laws now, all checked with `--verdict`, and `laws/mutants.sh` (run by `check.sh`, or alone) has 16
  mutants, all refused. A mutant of tensor-array's code is made in a copy of the published 0.1.16.0 that must still
  check by itself, so the refusal comes from these laws.
- `bands_len` and `matvec_l_len`, on tensor-array's own code: matrix · vector over bands gives one number per row.
  bend-ml had left the whole tree open (a band holds an `Array`, and the straight proof uses each band twice); here
  each step returns its result together with the proofs about it, in one record, so each band is used once.
- `fork_cover` (a model of tensor-fork's split): the blocks visit every row or column once, in order.
  `t8_rows_split` (real code) and `t8_blocks` (real leaves, model tree): the row blocks, run one after another, compute
  tensor-array's sequential product, the reason gemm-fork prints gemm-tile8's hashes, for the one product of three
  that splits by rows. Not proved: parallel against one after another (tensor-fork's `@unsafe` sharing), the U32
  offsets, the packing's blocks, and the order of writes in the column split.
- Two mutants are harmless to the result and still refused, as `s1 + s0` was: the right block running first, and the
  laws state the computation, not only its result. One the count laws let through: the bands' numbers joined in the
  other order (bend-ml's `join_len` refuses it).
- Not done: a count of each workload's output for the matrix products (C is written in place by index, with nothing
  for the checker to count but the loop's own steps).

## 2026-10-27: the three v1 branches together

- CI, the C targets and the laws merged into devel. On the merged tree: `make check` (eleven workloads on 1 and 16
  threads, eleven C targets, every hash its oracle), `make test`, `make laws` (six laws, 16 mutants refused) and
  `make mutate` pass. CI now runs `make laws` too.
- Three mutants for `lib/bt.h`, the layers of the three new C targets: RMSNorm without its epsilon and a causal mask
  one key short are caught; SiLU computed as x times the reciprocal instead of x over the sum survives, and so do
  SiLU with `expf` and SiLU plus 1e-7. `block-step` prints only each step's loss, and those changes move the loss by
  less than its last bit; a SiLU of zeros is caught. So the oracle of the whole-block workloads sees a layer's gross
  errors, not one rounding. Hashing the final weights as well would see them; that changes the oracle of every
  version, so it waits for the next run of all of them.
- `make mutate`: 52 mutants, 46 caught, 6 expected to survive.


## 2026-10-27: plan v1 step 2, launch day rehearsed (bits only)

- `ROUNDS=1 OUT=build/rehearsal ./release.sh 2.0.39` (a fresh clone of bendlang/bend, 2.0.38 and 2.0.39 built from
  their tags with bun 1.4.2) ran to the end, and every hash of its 55 cases (eleven workloads on both versions at 1
  and 16 threads, eleven C targets) was its oracle. Nothing upstream had changed how Bend builds. Its timings are
  thrown away: the machine was busy.
- But the run had not used the source builds. run.sh resolved the compiler inside the build's subshell, after its
  `cd` into the workload, so `build/bin/<n>` was never found and the installed 2.0.38 and 2.0.39 built every
  workload (env.tsv still named the wrappers, resolved outside it). On 2.0.40, which is not installed, every build
  would have failed, and then run.sh would have fed one empty case to the rounds and analyze.py would have stopped on
  it. Both fixed in run.sh. Run again with `BEND_38=/bin/false BEND_39=/bin/false`, so only the source builds could
  build: 22 builds ok, 55 hashes their oracles.
- release.sh: it now ends with `scripts/oracle_diff.py`, every case against `oracles.tsv` (a differing hash, a failed
  run, a workload with no oracle or no build), and exits 1 on any. The release before is now the previous `vX.Y.Z`
  tag in version order (2.1.0 found nothing before), `--previous` prints it, the source wrappers of installed
  versions are dropped even when run.sh stops (they would shadow the installed binaries afterwards), and a source
  tree removed by hand is pruned from the clone instead of stopping the next run.
- Tests: `tests/test_oracle_diff.py`, and `tests/test_release.py`, release.sh on a fake bendlang/bend (a local
  repository whose tags hold a `main.ts` that bun runs as `bend`), no network. Its two end-to-end cases need perf's
  P-core PMU and its others need bun, so CI's runner skips them. Each new test fails on the old scripts.
- The same bug was in the 2026-10-25 run (`results/2026-10-25-2.0.39/`): it measured the installed 2.0.38 and
  2.0.39, which are those releases, so its numbers stand; but release.sh's line that a source build counts the same
  instructions as the release was never measured by it, and is dropped until an idle run measures it.
- Left: run.sh names a version by its last number, so a 2.1.0 would be "0" and get the pre-2.0.38 thread option.
