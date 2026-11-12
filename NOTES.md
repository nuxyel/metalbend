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


## 2026-10-27: plan v1 step 3, gemm-fork under its C

Busy machine, instructions only, a diagnosis, not a result: these counts stay out of the README and `results/`. Bend
2.0.39 on one thread, `taskset -c 3`, 3 rounds of `run.sh` into a scratch folder; every hash its oracle, and every
count repeated to within 0.0001% between rounds (cycles moved by up to 15%).

| workload | Bend Minstr | C Minstr | Bend / C, instructions |
|---|---:|---:|---:|
| adamw | 17869.9 | 9244.0 | 1.93x |
| attention-step (new) | 19573.5 | 9008.2 | 2.17x |
| block-step (new) | 31400.6 | 14984.7 | 2.10x |
| gemm-fork (new) | 13906.9 | 8117.3 | 1.71x |
| gemm-tile8 | 13769.2 | 8121.9 | 1.70x |
| matvec-bands | 10634.6 | 3258.5 | 3.26x |
| mnist-step | 15939.1 | 6326.0 | 2.52x |
| read-binary (new) | 21.2 | 11.8 | 1.80x |
| read-native | 600.2 | 11.8 | 51.0x |
| rmsnorm-step (new) | 11815.6 | 1752.4 | 6.74x |
| softmax-ce | 7819.2 | 1603.0 | 4.88x |

(gemm-fork's C count is its new blocked target, below; against gemm-tile8's C, 8121.9, it was 1.71x too.)

- **gemm-fork's 0.94x is fewer cycles, not fewer instructions.** Its Bend runs 1.0% *more* instructions than
  gemm-tile8's (13906.9 M against 13769.2 M: the fork tree, the packing in blocks and the column loop), and 14% fewer
  cycles (2.56-2.61 G against 3.02-3.04 G in the same minutes; IPC 5.3 against 4.6). The cause is the order of the
  cells. At par 3 tensor-fork splits each product into 8 blocks, by columns when C is wider than tall: nt
  (256 x 1536) and nn (256 x 576) run every row of C over 1/8 of the columns at a time, so the block's packed lines
  of B (442 KB) stay in the 2 MB L2 while A's rows go by. tensor-array's sequential order, which gemm-tile8 runs,
  streams all of packed B (3.5 MB) once per row of C. tn (1536 x 576) splits by rows, which is the sequential order.
  `mem_load_retired.l2_miss/u`: 58-76 M in gemm-tile8's Bend, 0.25-0.36 M in gemm-fork's.
- **The C target was the plain order.** gemm-fork's `native.c` included gemm-tile8's, so the 0.94x compared a blocked
  Bend loop with an unblocked C loop. It now runs tensor-fork's blocks (8, halved as `cpar` and `rpar` halve them),
  the same cells and the same bits. The blocking does much less for C: its plain order already misses L2 only 3-5 M
  times (against Bend's 58-76 M; why the prefetcher keeps up with C's stream and not with Bend's is not read here),
  and the blocked C takes 2.25-2.28 G cycles against 2.27-2.51 G for the plain one, within this machine's noise. So on
  this run gemm-fork is about 1.15x its blocked C in cycles, near gemm-tile8's 1.30x less the cache gain Bend gets
  from the blocks. In my own 3-round run the old pairing gave 1.13x, not 0.94x: the C's cycles move most with the
  load, plausibly because its plain order leans on L3 (shared with whatever else runs) where the blocked loops sit in
  L2.
- Left for the idle run: the cycle ratio of gemm-fork against its blocked C, and whether a busy L3 is what moved the
  old pairing to 0.94x.

## 2026-10-27: plan v1 step 5, a count law for the products

- Result: gemm-tile8's product writes n x m cells of C, each (row, column) once, row by row, proved on tensor-array
  0.1.16.0's own code from `gemm_any` down (par 0, two rows or more). `make laws`: ten laws, 22 mutants refused.
- C is an `Array` written in place, with no length to count, so the laws count the writes: `laws/cells.bend` lists
  them (the only model), and each write runs tensor-array's `t8_cell` and `t8_set`. `t8_cols_cells` and
  `t8_rows_cells`: the column and row loops are exactly those writes, in order; `cells_len`: n x m of them;
  `gemm_t8_cells`: the entry point gemm-tile8 calls packs A and B and then does them. The proof carries each result
  with its two descriptions in one record, as `bands_len` does, because the arrays can be used once.
- Six mutants: four in tensor-array's code (every other cell, one cell fewer a row, starting at row 1, two-row
  products off the Tile8 path), one in the list (the first row n times, which keeps the count and only the law about
  the real code refuses), one in the statement.
- Not proved: that the U32 index of each write is a different cell of C (U32 and the array's mask both wrap; nothing in
  the corpus comes near), the one-row scalar path, and gemm-fork's tree over shared arrays. Its leaves are covered:
  row blocks are `t8_rows` from any row, column blocks run `t8_cols` from any column.

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

## 2026-10-27: toward v1.0.0, step 4, a GPU lane

- Three GPU targets, each a `gpu.bend` next to its workload's `main.bend`: `gemm-tile8` through bend-ml-tensor-gpu
  0.1.4.0 (`lib/gemm_gpu.bend`; 0.1.4.0 rather than 0.1.5.0 because it keeps gemm-tile8's tensor-array 0.1.16.0, and
  0.1.5.0 adds only the random fills), and `rmsnorm-step` and `block-step` with bendtorch-gpu 1.1.1.0 in place of
  bendtorch-fast 1.1.1.0, the import line alone changed, as BendTorch builds its GPU demos. `attention-step` is left
  out: `block-step` contains it. No CUDA of mine; the device code is what Bend makes of the packages' bangs.
- The same hashes on the RTX 4050 as on the CPU: gemm-tile8 `0c6d7fee9a7ddf37`, rmsnorm-step `50b8958aa3a54a76`,
  block-step `4afdd96850039587`, with nvrtc 12.9 and 13.4 alike, and with `+RTS --gpu off -RTS` on 1 and 16 threads.
  The products and the RMSNorm match by construction (tensor-array's order of additions, the CPU layers' expressions,
  no fused multiply-add on the device). block-step matches only because its oracle hashes the two losses: SiLU and the
  softmax take CUDA's float `exp` on the device, whose last bit differs from the host's on some inputs. Once the
  whole-block workloads hash their weights (step 1), block-step's `:gpu` oracle is expected to part from the CPU's, and
  its line in `oracles.tsv` then holds the device's hash, recorded as such.
- The GPU oracle is its own line, `<name>:gpu` in `oracles.tsv`; `make check-gpu` (local) builds each `gpu.bend` with
  CUDA, refuses a binary that does not link libnvrtc, and checks it on the device against `<name>:gpu` and with
  `--gpu off` against `<name>`: 9 runs, every hash its oracle. With no toolkit or no GPU it says why and passes (a test
  fakes a driver that sees no GPU); `make check` does not touch the GPU targets.
- `GPU=1 ./run.sh` builds the GPU targets with each version and runs them in the same rounds: the wall time of a plain
  run, then the kernels' time on the device from `nsys profile --trace=cuda`, into `gpu.tsv`; `analyze.py` adds a
  table and flags a GPU output that differs from the CPU's, between rounds or between versions. A one-round smoke run
  on a busy machine worked end to end; its times are not results, and the kernel times wait for the launch-day run.

## 2026-10-27: plan v1 step 1, the block workloads hash their final state

- `block-step`, `attention-step` and `rmsnorm-step` now print, after the losses, one hash of the final weights and
  both AdamW moments: `Layer.store` copies each into one array (weights, then m, then v, in the layers' dump order)
  and `lib/mb.bend`'s hash reads it. The gradient is left out, since the step zeroes it and the moments hold it. The C
  targets fold the same cells in the same order (`mb_fnv` in `lib/mb.h`, `bt_show_state` in `lib/bt.h`). The losses
  keep their bits.
- Oracles: attention-step `02e1fbcd81ca2848` -> `bb7f7e1c79c25bb7`, block-step `4afdd96850039587` ->
  `400cae69095e09cf`, rmsnorm-step `50b8958aa3a54a76` -> `37901ab4cff27378`, the same on Bend 2.0.35-2.0.39 at 1 and
  16 threads and on each C target (one bits-only round on a busy machine; no timings).
- The hash runs once, at the end: on 2.0.39 it adds about 0.8% of block-step's user instructions (3.5 M weights, so
  10.6 M numbers copied and hashed), 0.4% of attention-step's and nothing visible in rmsnorm-step's.
- `make mutate`: the three SiLU rounding mutants (x times the reciprocal, `expf`, plus 1e-7) are caught now, and two
  new mutants of the hash itself (the second moments left out, in C and in Bend) are caught. 56 mutants, 51 caught,
  5 expected to survive (four equivalent, one no run reaches). Result: the whole-block oracle sees one rounding
  inside a layer.

## 2026-10-27: block-step's GPU oracle parts from the CPU's once the weights are hashed

- After merging the state hash (plan-v1 step 1) with the GPU lane (step 4), `gpu.bend` of rmsnorm-step and block-step
  were made again from their `main.bend` (the import line alone changed).
- rmsnorm-step on the GPU: `37901ab4cff27378`, the CPU's. block-step on the GPU: `015f98a384541840`, against the CPU's
  `400cae69095e09cf`; the two losses keep their bits, the final state differs, as expected from CUDA's float `exp` in
  SiLU and the softmax. Three runs and both toolkits (CUDA 12.9, 13.4) gave the same hash, and `--gpu off` gives the
  CPU's on 1 and 16 threads. Result: `block-step:gpu` is the device's hash in `oracles.tsv`; `make check-gpu` passes.

## 2026-10-27: the format 1.x keeps, and the version numbers

- `docs/format.md`: what a workload is, the oracle (the first 16 hex digits of SHA-256 over the whole output,
  `<name>:gpu` for a GPU target), every file a run writes with its columns, and the steps to add a workload.
  `docs/VERSIONING.md`: MAJOR when old results can no longer be compared, MINOR for a new workload, target, lane or
  law, PATCH for fixes and a new Bend release's results.
- CI pushes on `main` and `devel` only. clang stays unpinned: `env.tsv` records its version on every run, and CI checks
  the bits with the runner's clang 18. Result: v1.0.0 is ready to tag; it waits for the 2.0.40 run.

## 2026-10-28: Array.get_unchecked on main (probe branch, `probes/1781/`)

- bendlang/bend#1880 (`Array.get_unchecked`, on main, not released): the dot of `repros/dot_mask_standalone.bend`,
  matvec-bands and gemm-tile8 with their loop reads unchecked, the same bits, on a source build of main 4f99f4c1.
  Instructions against C, busy machine: dot 1.67x -> 0.71x, matvec-bands 3.26x -> 3.01x, gemm-tile8 1.70x -> 1.30x;
  checked main counts what 2.0.39 counts.
- The scalar dot reads one number past each line, which the unchecked read must not be given at a capacity; the shape
  that stops before it (`km1`) costs matvec-bands 11% more checked, and the mask alone is 1.2-2.0 G of its 7.4 G to C.
- Timings wait for an idle machine (`probes/1781/README.md`).

## 2026-11-01: the harness before launch day (stale binaries, a fixed 2.0.39, preflight, launch.sh)

- Stale binaries: `run.sh` reused any binary in `build/` (`build/39/` and `build/c/adamw` were from 10-25, before the
  final-state hashes of 10-27). It now builds a binary again when its `main.bend`, `native.c` (and what it includes),
  `gpu.bend`, a file of `lib/` or its compiler is newer, and ends with `scripts/oracle_diff.py` (exit 1 on any
  difference). `release.sh` also clears `build/c` and `build/gpu-*`. `oracle_diff.py` listed every `<name>:gpu` line
  as missing on a CPU run, so a real `release.sh` would have failed since the GPU oracles went in; it now checks the
  GPU targets of a `gpu.tsv` against them and asks for them only then.
- "39" is `~/.bend-2.0.39/bin/bend`, a copy of the release next to 2.0.37 and 2.0.38's (the same SHA-256 as
  `~/.bend/bin/bend` today), no longer `~/.bend/bin/bend`, which the next `setup.sh` moves. Every version must report
  the release it names before anything builds, or `run.sh` stops. Names: 2.0.x by its last number, from 2.1 on the
  full version (`2.1.0`), in run.sh, release.sh, analyze.py, chart.py, oracle_diff.py and `docs/format.md`.
- `scripts/preflight.sh` (mains, profile, load under 2.0, other Bend or agent processes, `perf_event_paranoid`, CPU
  3's SMT sibling, which this kernel lists as CPU 4); its lines and a `busy` key go to `env.tsv` with the governor,
  `no_turbo`, THP, bun, each version's source (commit or binary hash) and a content hash of every imported package
  (`scripts/packages.py`). `analyze.py` prints the machine and marks a busy run at the top of `summary.md`.
- New: `scripts/bend_main.sh`, `scripts/report.py`, `scripts/launch.sh` (`make launch VERSION=...`),
  `scripts/bump_bend.sh`, `probes/1781/build.sh`, and a weekly, non-blocking `.github/workflows/main.yml`.
- Bend main faeb02ea (2026-10-31, still reports 2.0.39): `make check` 33 runs and `make check-gpu` 9 runs, every hash
  its oracle; nothing moved since 2.0.39. The #1781 probe's binaries built by `build.sh` on 2.0.39 and on main print
  the hashes of the 10-29 idle round.
- Source build against the released binary, 2.0.39 (busy machine, load 5-10; instructions only): the two compilers
  emit the same `.text`, `.rodata` and `.data` for gemm-tile8, softmax-ce, adamw, matvec-bands and block-step (the
  files differ only in the C file's name in the symbol table), and three rounds under `taskset -c 3` count the same
  user-mode instructions within 5,000 of 7.8-17.9 G: softmax-ce 7,819.20 M, adamw 17,869.92 M, gemm-tile8 13,769.19 M,
  matvec-bands 10,634.62 M on both. Result: a source build stands for the release in `release.sh`.
- Launch rehearsed: `BUSY_OK=1 ROUNDS=1 OUT=<scratch> scripts/launch.sh 2.0.39` ran end to end in 11 min (preflight
  busy, so marked; `check-gpu` 9 runs; both versions built from their tags; 61 cases, every hash its oracle, GPU
  targets included; the probe skipped, since v2.0.39 lacks a888ef27; chart and `report.md` written). Its timings are
  thrown away and the folder deleted. Left: `analyze.py` still lists block-step's GPU output as differing from the
  CPU's, which its `:gpu` oracle already records as expected.

## 2026-11-01: does a busy L3 move Bend's cycle ratio against C? (`probes/l3/`, idle machine)

The question left on 10-27. Bend 2.0.39, one thread on CPU 3, gemm-fork and gemm-tile8 and their C targets, each
with and without a streaming loop on the E-cores that share the L3 (CPUs 12-19, 64 MB each), alternated rounds,
`mem_load_retired.l3_miss/u` counted too; 4 blocks of 5 rounds, every hash the oracle. Preflight: load 0.60-1.28,
mains, `performance`, CPU 3's sibling 0-1%; two idle agent sessions (under 3% of a CPU) the only other processes.
`scripts/preflight.sh` now reads the load average before its other checks start their processes.

| Bend / C, cycles | idle | 8 streams (67 GB/s) | 2 streams (35 GB/s) | 1 stream |
|---|---:|---:|---:|---:|
| gemm-fork / its blocked C | 1.14x | 1.13x (-0.8%) | 1.13x | 1.13x |
| gemm-fork / gemm-tile8's plain C | 1.13-1.14x | 1.01-1.02x (-10 to -12%) | 1.14x | 1.13x |
| gemm-tile8 / its plain C | 1.34x | 1.24-1.26x (-6 to -7%) | 1.32x | 1.34x |

- Yes, in the direction guessed: with eight streams the plain C takes 1.21-1.23x its idle cycles, the blocked loops
  1.09-1.10x and gemm-tile8's Bend 1.14x, so every ratio against the plain C falls 6-12% and the blocked pair moves
  under 1%. Idle, none of the four misses the L3 (under 0.04 M); with eight streams 0.2-2.6 M.
- It does not explain the 0.94x: the old pairing's lowest round is 0.994x. What else the 10-27 machine did (compilers
  on the P-cores at load 5-10) is not reproduced here.
- For the launch run: one or two streams leave every ratio within 1% and every program within 3% of its idle cycles;
  eight move a ratio by up to 12% while each of them is a runnable process, which the preflight's load average under
  2.0 sees on a sustained load. The requirement stands as written (an idle machine, preflight clean); the blocked
  pair, gemm-fork against its own C, is the ratio that holds even on a loaded L3. The cycle ratio of record for
  gemm-fork against its blocked C is 1.14x (10-27's busy estimate was 1.15x).

## 2026-11-01: docs for a reader from outside, the pinned CPU and the PMU as variables

- Each workload has a `README.md` (what it computes, its package, its C and GPU targets, its oracle, its mutants), and
  the README has "Reading a run" (summary.md from top to bottom) and "On another machine" (perf events, the pinned CPU,
  where each Bend version is found).
- `scripts/pmu.sh`: `CPU=<n>` pins the one-thread runs (3 by default) in `run.sh`, `probes/l3/run.sh` and
  `probes/1781/count.sh`, and the PMU is detected: `cpu_core` (`cpu_atom` for an E-core, both PMUs on more threads) on a
  hybrid Intel CPU, plain `cpu` elsewhere. `env.tsv` gains `cpu_pinned` and `pmu`; the preflight's sibling check
  follows the CPU (`cpu3_sibling` by default, so the keys of a default run do not change). Tests on fake PMU trees and
  with stand-in `perf` and `taskset`. Nothing measured: the default run counts the same events as before.
- `analyze.py` no longer lists block-step's GPU output as a finding: a GPU output that differs from the CPU's is
  expected when the GPU printed its `<name>:gpu` oracle, the CPU its `<name>` oracle, and the two lines differ. Any
  other split is still a finding (tests for each case).

## 2026-11-01: four new workloads for 1.0 (bits and oracles; timings at the next idle run)

Written on a branch of their own for 1.1; Renan put them in 1.0 the same day, so 1.0 has fifteen workloads. Each one
has a C target, an oracle line from a `ROUNDS=1 THREADS="1 16"` run of 2.0.35-2.0.39 and its C (every hash one), and
mutants. Busy machine: no timings.

- `softmax-ce-array`: softmax-ce's program on tensor-array 0.1.18.0 (rows read in place since 0.1.17.0). Prints
  softmax-ce's hash, `debeda8b7bc50c1f`, so its C target is softmax-ce's, included.
- `mnist-fork`: mnist-step with its five products through tensor-fork 0.1.5.0 (on tensor-array 0.1.18.0). Prints
  mnist-step's hash, `2d83be930d21fb9f`, and its C target is mnist-step's. The products' depth is an equivalent mutant.
- `read-bf16`: two SmolLM2-135M decoder layers (18 tensors, 7,080,192 numbers) in a 14 MB BF16 safetensors file
  (`lib/gen_bf16.py`, `make data`; run.sh and the check write it when it is missing), read in the model's order with
  bendtorch-load 1.2.0.0's `tensors`: the header lexed and parsed in Bend, each tensor read by bend-ml-binary-read's
  BF16 effect. Oracle `d09cf49a5e86a7f6`. It does not build on 2.0.35, like read-binary: the package's C effect does
  not compile against that runtime (`io_eff` took another signature).
- `bpe-encode`: bend-ml-bpe-tokenizer 0.1.3.0 trains 256 merges on 4,096 words of synthetic text (a hashed vocabulary
  of 64 words, skewed toward the first) and encodes 32,768 more words; prints the rule count, the token count (31,633)
  and an FNV-1a hash of the ids. Its C target counts pairs in a table indexed by the two ids, with the first-appearance
  tie-break of the package. Oracle `770398c19951fa8c`.
- `lib/ta18.bend`: lib/ta.bend's helpers at tensor-array 0.1.18.0, since a `Mat` of one version is not one of another.
- `make mutate`: 13 new mutants (12 caught, the depth one equivalent), 70 in all.

## 2026-11-01: launch day rehearsed on 2.0.39, 5 rounds (`results/2026-11-01-2.0.39-rehearsal/`)

Renan's call: a full dress rehearsal on 2.0.39 with the fifteen workloads, timed; the run of record stays the 2.0.40
launch run. `BUSY_OK=1 ROUNDS=5 OUT=results/2026-11-01-2.0.39-rehearsal scripts/launch.sh 2.0.39`, 2.0.38 against
2.0.39 from their tags, 1 and 16 threads, C and GPU targets, about 15 min. Preflight clean but for four idle agent
processes (three Codex at 0.0% CPU, the Claude Code session driving the run under 3.5%), so `env.tsv` says
`busy other_processes`; load 1.02-2.68 before the runs, round means 1.50, 1.09, 1.82, 1.59, 1.59. 405 runs, every hash
its oracle (`make check-gpu` 9 more). Instructions repeat to 0.00% between rounds everywhere.

| Bend 2.0.39 / C, one thread | cycles | instructions |
|---|---:|---:|
| gemm-fork (its blocked C) | 1.13x | 1.71x |
| softmax-ce-array | 1.18x | 1.69x |
| adamw | 1.18x | 1.93x |
| read-binary | 1.20x | 1.80x |
| block-step | 1.23x | 2.11x |
| gemm-tile8 | 1.34x | 1.70x |
| mnist-fork | 1.39x | 2.12x |
| attention-step | 1.41x | 2.18x |
| read-bf16 | 1.80x | 5.81x |
| mnist-step | 1.91x | 2.52x |
| matvec-bands | 2.37x | 3.26x |
| rmsnorm-step | 3.62x | 6.74x |
| softmax-ce | 4.51x | 4.88x |
| read-native | 19.0x | 51.0x |
| bpe-encode | 463x | 645x |

- gemm-fork against its blocked C: 1.13x (2552.0 M against 2257.3 M cycles), the L3 probe's idle 1.14x again; against
  gemm-tile8's plain C (2261.9 M) also 1.13x, since idle the two C loops take the same cycles.
- The four new workloads' first timings: softmax-ce-array, the same program as softmax-ce on tensor-array 0.1.18.0,
  runs 2.89x fewer instructions and 3.85x fewer cycles than it (2,703.9 M against 7,819.2 M; 1.18x C against 4.51x).
  mnist-fork 1.39x against mnist-step's 1.91x, with 16% fewer instructions. read-bf16 1.80x. bpe-encode 463x its C
  (33.1 G cycles against 71.6 M): the package's training and encoding against a table indexed by the two ids, the
  largest gap in the corpus, not read further here.
- 2.0.38 against 2.0.39: beyond noise only softmax-ce (+183% instructions), mnist-step (+37%) and mnist-fork (+2.87%
  instructions, +5.3% cycles, new); the rest within 0.02% in instructions.
- 16 threads over one (2.0.39, wall time): matvec-bands 4.41x, block-step 4.08x, attention-step 3.59x, gemm-fork
  2.12x, mnist-fork 1.12x; the rest 0.94-1.03x but read-binary 0.71x and read-native 0.66x. The thread guard saw 1 and
  16 on both versions.
- GPU kernel time (nsys, 2.0.38 / 2.0.39): block-step 208.9 / 204.6 ms (345 kernels), gemm-tile8 53.4 / 54.0 ms,
  rmsnorm-step 3,273.8 / 3,272.3 ms (5,000 kernels).
- Two harness bugs the rehearsal found, both fixed with a test: `chart.py` had no labels for the four new workloads
  (a KeyError, so launch day would have had no chart), and `launch.sh` passed its `OUT` to `make check-gpu`, whose
  `check_oracles.sh` builds into `$OUT`, so the GPU binaries landed in the results folder (removed before the commit).
  The chart of this run is in the folder; `docs/results-2.0.39.svg` is unchanged.
- The run of record remains 2.0.40's, on launch day; these numbers do not fill its blanks.

## 2026-11-06: the launch run on 2.0.40, with agent sessions open (`results/2026-11-06-2.0.40-diagnosis/`)

`scripts/launch.sh 2.0.40`, 5 rounds, from a night script after a 30-minute wait for a clean preflight; the only busy
check was two idle Claude Code sessions, so `BUSY_OK=1` and the run is a diagnosis, not the run of record (renamed so
`results/<date>-2.0.40` stays free for it; `docs/` untouched). Load 1.10 at the start. Every hash its oracle (81
cases). Instructions repeat to 0.00% between rounds, so their changes stand:

- 2.0.40 runs fewer instructions than 2.0.39 on thirteen workloads: rmsnorm-step -29.4% (cycles -30.2%), read-bf16
  -40.5% (cycles -16.8%), softmax-ce-array -8.5%, mnist-fork -5.9%, adamw -5.8%, the rest -1.7% to -2.9%.
- **bpe-encode regresses: +9.3% instructions, +28.1% cycles (7.37 to 9.44 s), same output.** gemm-fork +0.9%
  instructions. To look at before the run of record.
- Bend / C in cycles, one thread, 2.0.39 to 2.0.40: rmsnorm-step 3.62x to 2.52x, read-bf16 1.81x to 1.51x,
  softmax-ce-array 1.17x to 1.09x, adamw 1.19x to 1.14x, mnist-fork 1.37x to 1.29x; bpe-encode 475x to 609x.
- 16 threads over one: matvec-bands 4.35x to 5.15x, block-step 4.07x to 4.74x, attention-step 3.65x to 3.93x.
- GPU kernels: block-step 207.5 to 178.3 ms (-14%), rmsnorm-step -5.5%, gemm-tile8 +3.5% (inside its 10% spread).
- The #1781 probe (`probe-1781.tsv`, medians of 5): the dot with `get_unchecked` 0.073 s against 0.121 s checked and
  0.070 s for its C; matvec 0.451 s against 0.535 s (C 0.239 s); gemm 0.522 s against 0.648 s (C 0.506 s).

## 2026-11-06: bpe-encode's regression on 2.0.40 is two upstream commits

The two commits were found by bisecting bendlang/bend between the tags, counting instructions and L1 load misses on
one pinned thread. Each was checked by undoing it in 2.0.40's emitted C, and #1978 in the compiler too. Every build
printed the oracle's hash.
- bendlang/bend#1978 (0d35f6da, the Metal fix for #1954) accounts for the instructions, 177.9 G to 196.3 G. On the host,
  every take of a node with the RFC bit now calls `span_fade`: a plain `noinline`, where 2.0.39 did the last-holder
  free inline. 1.21 G calls against 39.5 M. With the take as in 2.0.39, 2.0.40 runs 173.6 G instructions, 2.3% under
  2.0.39.
- bendlang/bend#2036 (3c1f0d3a) accounts for most of the remaining cycles. Instructions go down 1.1%, but L1 load misses
  in `bump.go`'s walk over the pair counters go from 0.22 G to 1.24 G. It comes from `merge.go`, which now keeps a
  token boxed instead of building it again. Why that layout misses is not proven.
- With both undone, 2.0.40 is back to 2.0.39: 177.1 G instructions, 33.9 G cycles against 33.7 G.

An upstream draft is in my private notes. Upstream main still has both.

## 2026-11-06: the preflight and idle agent sessions

- Until today any `claude`, `codex` or `opencode` process made the machine busy, so an agent session left open and
  idle turned a run of record into a diagnosis (the 2.0.40 run of 00:54, two idle sessions open, load 0.00). Renan's
  call: an idle session is not work. With `AGENTS_IDLE_OK=1` the preflight samples each agent's whole process tree
  (every descendant, so a build it starts counts) and lets it through under `AGENT_MAX_PCT` (2%) of one CPU over the
  sample; a Bend compiler is still busy. The default is the old rule. `env.tsv` keeps the line, e.g.
  `claude x2, agents idle 0.4%`, so a run says what was open.
- `scripts/when_idle.sh <command>` runs the preflight every minute and starts the command after five passes in a row.
  The 2.0.40 run of record waits on it, detached, with `AGENTS_IDLE_OK=1`.
- Calibrated the same day: two idle Claude Code sessions use 2-5% of one CPU in a one-second sample (the threshold
  of 2% never let five minutes pass in a row) and 4.9% over 30 s; a build uses 100% or more. The run of record
  waits with `AGENT_SAMPLE=10 AGENT_MAX_PCT=10`, 10% of one CPU being under 0.5% of the machine, on cores other
  than the pinned one. Its first two starts stopped at `make check-gpu`: `check_oracles.sh` wants its pinned Bend
  2.0.39 and `~/.bend` is 2.0.40 since that morning, so the unit sets `BEND=~/.bend-2.0.39/bin/bend`.

## 2026-11-06: the 2.0.40 run of record (`results/2026-11-06-2.0.40/`, 11:19-11:34)

- `scripts/launch.sh 2.0.40` through `scripts/when_idle.sh`, as a user unit, with `AGENTS_IDLE_OK=1`: the preflight
  found the machine idle (load 0.50, two Claude Code sessions open at 1.3% of one CPU, CPU 3's sibling at 0%), and
  `results/2026-11-06-2.0.40/` is the run of record; the diagnosis of 00:54 stays as `-diagnosis`. 81 cases, every hash
  its oracle; `make check-gpu` with the pinned 2.0.39 (`BEND=~/.bend-2.0.39/bin/bend`).
- Against 2.0.39, 5 rounds: fewer instructions on 12 of the 15 workloads (`rmsnorm-step` -29.42% and -30.22% cycles,
  `read-bf16` -40.53% and -17.15%, `softmax-ce-array` -8.45%, `mnist-fork` -5.90%, `adamw` -5.84%); `read-binary`
  unchanged; `gemm-fork` +0.90% instructions (+2.97% cycles, within its noise); `bpe-encode` +9.26% instructions and
  +28.89% cycles, the same as the diagnosis (+9.3%, +28.1%): its cause, bendlang/bend#1978 and #2036, is in the entry
  above. On the GPU, `block-step`'s kernels 205.9 to 179.3 ms (-12.93%), `gemm-tile8` and `rmsnorm-step` within noise.
- The #1781 probe on 2.0.40: the gemm with unchecked reads 10,194.7 M instructions and 2,339-2,349 M cycles against
  13,443.7 M and 2,906-2,928 M checked, and C's 8,121.9 M and 2,242-2,249 M (1.04x C's cycles against 1.30x); the dot
  product's in-range unchecked loop 299-304 M cycles against 513-517 M checked and C's 288-291 M (1.04x against 1.78x).
- Threads: the same bytes at 1 and 16; `matvec-bands` 4.86x, `block-step` 4.66x, `attention-step` 4.06x, `gemm-fork`
  2.24x (4.33x, 4.08x, 3.52x, 2.05x on 2.0.39 in this run).
- `docs/results-2.0.40.svg` is the README's chart now.

## 2026-11-06: the working pin to 2.0.40

- `scripts/bump_bend.sh 2.0.40` (the two Linux SHA256 are the release's asset digests): `setup.sh`, `check_oracles.sh`'s
  `PIN`, CLAUDE.md, the Makefile, CI's step, the README, and run.sh's default range, now 2.0.35-2.0.40. bend-ml,
  llama.bend and BendTorch moved the same morning, and `~/.bend` is the 2.0.40 release (2.0.39 in `~/.bend-2.0.39`).
- On 2.0.40: `make check` 45 runs and `make check-gpu` 9 runs, every hash its oracle (`oracles.tsv` unchanged); `make
  laws` ten laws, 22 mutants refused; `make mutate` 70 mutants as expected (64 caught, the same 6 survive); `make test`
  111. Two tests named 2.0.39 (the bump script's and the GPU check's fake compiler); they now read the pin from the
  repository, and the bump test moves it one release past the real one.

## 2026-11-07: the release watch (Cachegrind on GitHub's runners)

- `scripts/count.sh <Bend> <workload>`: a Bend from a ref (`scripts/bend_main.sh`, now with `BIN` for the wrapper's
  path), a binary or a source tree; the workload built once into `build/count/<commit>/`, run on one thread under
  `valgrind --tool=cachegrind --cache-sim=yes` with the caches given explicitly, and one row: instructions, simulated
  D1 and last-level misses, the hash against `oracles.tsv`. Under `env -i` with a fixed environment: on this machine
  `HEADER=1` alone in the environment moved `read-native`'s count by 241 instructions (the environment's size moves
  the stack); with it fixed the count repeats exactly whatever the caller's environment.
- `scripts/track.sh <old> <new> [workloads]`: both Bends built once, every workload counted with each, then
  `scripts/track_verdict.py`: a finding beyond 0.1% in instructions or 5% in D1 misses, or an output that is not its
  oracle; regression, improvement, mixed, same, bits, no-baseline, missing. `--next` and `--previous` read
  bendlang/bend's release tags in version order.
- `.github/workflows/track.yml`: daily, the first release after `track/last-tag` on the new `data` branch (it starts at
  v2.0.40) against the release before it; one job a workload, both Bends in the job, the counts appended to `track/`
  and an issue here on a regression or a changed output; by hand with any refs. `docs/format.md` has `track/`.
  `workflow_dispatch` needs the file on `main`, so before the release it ran from a throwaway branch with a push
  trigger once (to register it), then by its id on `devel`.
- The replay, v2.0.39 against v2.0.40 on all 15 workloads (run 42377905816, ubuntu-24.04, clang 18.1.3, valgrind
  3.22.0, `track/runs/2026-11-07-v2.0.39-v2.0.40/`): every output its oracle; `bpe-encode` the one regression,
  instructions +9.42% and D1 misses 2.03x (195,729 M to 214,161 M; 1,108 M to 2,246 M); 12 improvements (`read-bf16`
  -22.47%, `mnist-fork` -10.61%, `rmsnorm-step` -9.25%, `mnist-step` -8.10%, `softmax-ce-array` -4.94% the largest);
  `read-binary` and `read-native` the same. The runner's clang moves some counts against this machine's perf ones
  (`gemm-fork` -2.65% here, +0.90% in the run of record; `read-native` +0.00% here, -2.10% under Cachegrind with clang
  23.1.3 here), which is why the watch compares two Bends on one runner only.
- `make test` 133, from 111 (count.sh with a fake Bend and valgrind, track.sh's lookups, track_verdict.py);
  `make mutate` 75 mutants (five new ones on count.sh and track_verdict.py, all caught). For 1.1.0, with the next
  release.

## 2026-11-07: the history, Bend 2.0.32 to 2.0.40 under Cachegrind

- `scripts/history.sh <workload> <release>...`: one workload counted (`scripts/count.sh`) with every release of a range,
  one after another on one machine, so its whole line comes from one runner and one clang; a release where it does not
  build or run is a row of `gaps.tsv` with its first error line. `--releases <first> <last>` lists bendlang/bend's
  release tags in between. `scripts/history_report.py` judges each step from a release to the next as the release
  watch does (plus `gap` and `first`) and writes `steps.tsv`, `coverage.tsv` and `report.md`;
  `scripts/history_chart.py` draws `docs/history.svg`, one small chart a workload on its own scale (four workloads drop
  by about 70%, and one scale for all flattened the rest). `.github/workflows/history.yml`, by hand: a job a workload,
  then the report, into `history/` on the `data` branch (`docs/format.md`). One job a workload instead of the watch's
  pairs counts each release once (9 counts a workload, not 16) and keeps a workload's line on one machine.
- The run, https://github.com/nuxyel/metalbend/actions/runs/42381915783 (`history/2026-11-07-v2.0.32-v2.0.40/`): 15
  workloads, 9 releases, 127 counts, every output its oracle, and 8 gaps, `read-bf16` and `read-binary` on 2.0.32-2.0.35
  (binary-read's C effect against the older effect interface: `io_res` undeclared on 2.0.32, `too few arguments` on
  2.0.33-2.0.35). `bpe-encode`'s job, 9 cache-simulated passes, took the longest. Its 2.0.39 and 2.0.40 counts
  against the release watch's replay on another runner: 28 of 30 the same to the instruction, `read-bf16`'s two 403
  instructions apart (0.0003%).
- What moved (instructions, one thread, the runner's clang 18): 2.0.33 cut `gemm-fork` to 0.26x, `block-step` 0.29x,
  `mnist-fork` 0.30x and `attention-step` 0.33x (the workloads that split their work into parallel blocks; locally,
  `gemm-fork` with `--threads 1` takes 1.79 s of user time on 2.0.32 and 0.55 s on 2.0.33, one thread each, the same
  hash, on a busy machine); 2.0.36 `bpe-encode` -7.98% and `rmsnorm-step` -6.73%; 2.0.39 `softmax-ce` 0.41x and
  `mnist-step` -28.18%; 2.0.40 12 of 15 fewer and `bpe-encode` +9.42%. Small regressions: `bpe-encode` +0.42% and
  +0.12% (2.0.37, 2.0.38), `softmax-ce` +0.31% and +1.83%, `gemm-fork` +0.22% and `mnist-fork` +0.59% (2.0.36),
  `mnist-step` +0.14% (2.0.37). From 2.0.32 to 2.0.40: the four parallel-block workloads 0.26-0.31x, `softmax-ce`
  0.40x, `mnist-step` -34.28%, `rmsnorm-step` -15.75%, `read-bf16` -24.16% (from 2.0.36), `bpe-encode` +1.23%,
  `read-native` and `read-binary` unchanged. Which commits of 2.0.33 made the parallel-block change is the bisect's
  question.
- Cycles on 2.0.32-2.0.34 need an idle machine: `scripts/history_cycles.sh` builds those three from their tags and runs
  the corpus with 2.0.35 in the same rounds (1 and 16 threads, 5 rounds, no GPU) into `results/<date>-2.0.32-2.0.34/`.
  Not run yet. When the machine is idle, from a user unit so that no agent's process tree holds it:

  ```sh
  cd ~/Repos/Bend2/metalbend
  systemd-run --user --collect --unit=metalbend-old-cycles --working-directory=$PWD \
    --setenv=AGENTS_IDLE_OK=1 --setenv=AGENT_SAMPLE=10 --setenv=AGENT_MAX_PCT=10 --setenv=BEND_NO_TELEMETRY=1 \
    --setenv=MAX_WAIT=12 --setenv=PATH="$PATH" \
    -p StandardOutput=append:$PWD/build/when_idle.log -p StandardError=append:$PWD/build/when_idle.log \
    $PWD/scripts/when_idle.sh $PWD/scripts/history_cycles.sh
  ```
- `make test`: 10 more tests (history.sh on fake Bends, history_report.py, history_chart.py). For 1.1.0, with the next
  release.

## 2026-11-07: the bisect (`scripts/bisect.sh`, `.github/workflows/bisect.yml`)

- `scripts/bisect.sh <workload> <good> <bad> [ir|d1|bits]`: `git bisect run` in a `--no-checkout` worktree of the
  bendlang/bend clone, each step `scripts/bend_main.sh` at the commit and one `scripts/count.sh`, judged by
  `scripts/bisect_report.py`: bad when the count is nearer the bad end's than the good end's (more than half the
  way), so a commit that moves a little does not decide a bisect over a big change, and an improvement bisects the same
  way; a commit whose Bend or workload does not build, or whose output is not its oracle, is skipped (for `bits`, a
  changed output is bad). The counts are shared between the metrics of one run. Then the report: the commit, its pull
  request (`gh api`), Cachegrind's counts per function at the parent and at the commit, and the C both emit for the
  workload, diffed by definition (a top-level definition, or a `WL_CASE` block for the program's own functions).
  `git bisect run` hands the step the bisect's repository in `GIT_DIR`; the step clears it, or every count would name
  the bisect's HEAD as its commit.
- `bisect.yml`: by hand or called by `track.yml`, which now bisects every regression or changed output it finds (the
  metrics that went up) and opens the issue after, naming the commits. The issue names the pull request in a code
  span, not a link: a link from an issue would put a "mentioned this" on its timeline in bendlang/bend. Registered for
  `workflow_dispatch` from a throwaway branch whose push run skips, as `track.yml` was. `track.yml`'s gather found no
  counts when one workload ran: download-artifact puts a single artifact straight into its folder; it finds them now
  wherever they are.
- On this machine first (busy; Cachegrind's counts do not mind): `rmsnorm-step` from v2.0.39 to v2.0.40, instructions
  -28.58% with clang 23.1.3, is bendlang/bend#1928 (`blk_new`'s fill vectorized), 7 steps over 118 commits in 3 min.
- On a runner (ubuntu-24.04, clang 18.1.3, valgrind 3.22.0), from `track.yml` on `bpe-encode` (run 42384646460, the
  bisect 1 h 56 min, `track/regressions/v2.0.40-bpe-encode-{ir,d1}/`):
  - instructions: 0d35f6da (#1978, "On Metal, the shared-node half of a take is a call"), +7.84% at that commit,
    +9.42% over the range, 7 steps; `span_fade` 1.11 G to 28.05 G instructions, the workload's `bump_go` -10.2 G and
    `peek` -0.94 G; the C changed in `span_fade` and `ctr_take`.
  - D1 misses: 3c1f0d3a (#2036, "a wide def's boxed record stays boxed until a use needs it"), 2.03x at that commit
    and over the range, 6 steps; `bump_go` +552 M, `rfc_wrap` +393 M, `bump_go`'s continuation +165 M; the C changed
    in `bump_go`, `count_go`, `merge_go` and their continuations.
- `gemm-fork` from v2.0.32 to v2.0.33 (run 42387765688, by hand, `track/regressions/v2.0.33-gemm-fork-ir/`):
  ef66a7cc (#1155, "A shared Array's redirect is read without a race and without an atomic on the device, once per
  spin"), 0.26x the instructions at that commit and over the range, 4 steps over 24 commits in 6 min; `spin_8`
  49.1 G to none, the program's `cpar` +8.3 G and a new `spin_26` +4.3 G (2.0.33 numbers its spins anew, so the
  per-function table pairs some of them by name only).
- `make test`: 14 more tests (`tests/test_bisect.py`; 157 with the history's); `make mutate` 79 mutants (four new
  ones on `bisect_report.py`, all caught). For 1.1.0, with the release watch.

## Release v1.1.0: the release watch, bisect and the history from 2.0.32 (2026-11-07)

- PR #3, CI green, merged as 6324d5a, tag `v1.1.0`, GitHub release. `track.yml` is on main, so its daily run now
  checks bendlang/bend's tags; the `data` branch's `track/last-tag` is v2.0.40, so the first run that counts is
  2.0.41's. The throwaway "phase 0 probe" workflow is disabled.

## 2026-11-08: the history's cycles on 2.0.32-2.0.34 (idle machine)

- `scripts/history_cycles.sh` from `when_idle.sh` (01:14-01:28, preflight clean): 2.0.32, 2.0.33 and 2.0.34 built from
  their tags, with 2.0.35 in the same rounds, 1 and 16 threads, 5 rounds, into `results/2026-11-08-2.0.32-2.0.34/`.
  Its exit status is 1 because the oracle check counts the 8 missing runs of `read-bf16` and `read-binary` on 2.0.32
  to 2.0.35, which do not build before 2.0.36; every other case matches `oracles.tsv`, and every workload gives the
  same hash on the four releases.
- One thread against 2.0.35: on 2.0.32 the four parallel-block workloads take +163% (`attention-step`) to +227%
  (`gemm-fork`) cycles for +204% to +275% instructions, the #1155 change the Cachegrind history shows at 2.0.33;
  2.0.33 and 2.0.34 are within 3% in cycles. `rmsnorm-step` takes 13-14% more cycles on 2.0.32-2.0.34 for 0.5% fewer
  instructions, a move only cycles show. Nothing else moves beyond noise.
- 16 threads: 2.0.35 runs `attention-step` in 0.237 s against 0.327-0.329 on 2.0.33/2.0.34, and `block-step` in 0.337
  against 0.444-0.453, with the same one-thread time: a change in how the parallel blocks run, not in their work.

## Release v1.1.1: the history's cycles on 2.0.32-2.0.34 (2026-11-11)

- PR #4, CI green, merged as bb9f5db, tag `v1.1.1`, GitHub release. A results patch: the entry above, in the README's
  history section; the corpus, its oracles and its tools unchanged.

## Release v1.1.2: the README opens with what MetalBend found (2026-11-12)

- PR #5, CI green, merged as 7be64f5, tag `v1.1.2`, GitHub release. A documentation patch: the README opens with what
  MetalBend has found, each in a line with its number, and the history's chart moves to the top; the corpus, its
  oracles and its tools unchanged. The same day the repository's description and topics changed to say what it does
  (the release watch, the bisect, the history from 2.0.32).

## 2026-11-12: llama-token, the first workload of the second corpus

- **What.** `workloads/llama-token`: 32 positions, one token each, through `bend-ml-llama@0.2.1.1`'s `forward_gen`
  with the key/value cache, at SmolLM2-135M's widths with 2 layers and a vocabulary of 3,072 (the head is then a fifth
  of a token's products, as in the 135M). The other workloads time a kernel or a training step; this one times a
  token with everything around the products, the package's lists among them. The weights are `lib/mb.bend`'s values
  by cell, so they do not depend on the bands, and the band depth follows the thread count as llama.bend's does.
- **Bits.** It prints the hash of every position's logits; the oracle is `0a85f2fce42dcde7`, from Bend 2.0.40 on 1,
  2, 4, 16 and 22 threads (one band up to two threads, 16 above) and from `native.c`, which repeats the package's
  order of operations on arrays. `make check` runs it; `make test` passes.
- **Mutants.** Ten new ones: one position fewer and the second layer's seeds (Bend), and in the C target the keys
  and values swapped, a query head on the next key/value head's cache, attention one key short, RoPE's sign, SiLU's
  sign, RMSNorm's squares added from the left, a softmax without its maximum: all caught. Swapping the operands of
  the residual's addition survives, as it must.
- **Measured** the same day on an idle machine (19:12, nobody at it, in a round of measurements started after five
  quiet minutes), outside `run.sh`: one thread pinned to CPU 3 and counted by `perf stat` in user mode, 5 alternated
  rounds, medians. Bend 2.0.40 takes 3.282 G instructions and 0.841 G cycles (0.801 to 0.859) against the C target's
  1.145 G and 0.481 G (0.473 to 0.483): 2.87 times the instructions and 1.75 times the cycles, 0.192 s against 0.119
  s. On 4, 8, 16 and 22 threads it takes 0.099, 0.095, 0.105 and 0.109 s: threads halve the time and no more. All 30
  runs print the oracle.
- **Left for the release.** A run of record with it (its history starts at 2.0.40, the first release its package
  builds on), its label in `scripts/chart.py`, and the counts the README takes from the last run, which still say
  fifteen.
