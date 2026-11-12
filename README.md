# MetalBend

[![CI](https://github.com/nuxyel/metalbend/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/nuxyel/metalbend/actions/workflows/ci.yml)

Sixteen real machine-learning workloads for Bend 2's compiler, run on every Bend release. Each one is checked by its
exact output and measured against a handwritten C program that prints the same bits, and when a release makes one
slower, MetalBend finds the commit that did it.

![Fifteen small line charts, one per workload, of its instructions on Bend 2.0.32 to 2.0.40 against the first release it builds on. The parallel matrix product, the parallel MNIST step, the transformer block and attention drop by 67-74% at 2.0.33 and stay there; softmax and cross-entropy drops 59% at 2.0.39; the MNIST step falls 34% over 2.0.39 and 2.0.40; the BF16 read 24% from 2.0.36, most of it at 2.0.40; RMSNorm 16%; the BPE tokenizer falls 8% at 2.0.36 and rises 9% at 2.0.40, ending 1.2% above 2.0.32; the two file reads do not move.](docs/history.svg)

- **Every release, counted by itself.** Bend 2.0.40 runs fewer instructions than 2.0.39 on 12 of the 15 workloads and
  more on one, the BPE tokenizer (+9.42%, 2.03x the L1 data misses). The bisect found the two commits behind it,
  bendlang/bend#1978 and #2036, in 7 and 6 steps over 118 commits.
- **Nine releases of history.** From 2.0.32 to 2.0.40 no release changed a bit of any output. 2.0.33 cut the four
  parallel-block workloads to 0.26-0.33x the instructions (bendlang/bend#1155).
- **The distance to C.** On 2.0.40, from 1.09x C's cycles (softmax and cross-entropy over the array) and 1.13x (the
  AdamW step) to 2.50x (RMSNorm) and 4.47x (softmax and cross-entropy); 19x for the built-in file read and 611x for
  the BPE tokenizer.

I cut the workloads from my three Bend projects (bend-ml, llama.bend and BendTorch): matrix products, a banded
matrix-vector product, attention, normalization, an optimizer step, training steps, file reads, a tokenizer, a Llama's
whole token. GitHub's runners count each new release's instructions under Cachegrind, and my machine its cycles, 16
threads and the GPU, so a release that changes a workload's speed or its bits shows up as a number.

Renan Vinícius (@nuxyel).

## What a workload is

Each workload under `workloads/<name>/` has up to five parts:

- **The oracle.** The program prints a hash of its whole output. A faster build that changes one bit fails the
  oracle; a different hash is a finding, never noise.
- **The starting point.** `main.bend`, timed by `perf stat` (instructions and cycles in user mode, one thread pinned to
  one core) on every Bend version in the run, and by the wall clock on 16 threads.
- **The target.** `native.c`, where there is one: a handwritten C version with the same order of operations, so the
  same bits, and the distance from Bend to native code becomes a ratio. The C targets are the yardstick here, not
  library code: my packages stay in Bend, and these files exist to measure how far Bend's output is from C.
- **The GPU target.** `gpu.bend`, for three workloads: the same program through the GPU lanes of my packages
  (bend-ml-tensor-gpu's products, BendTorch's GPU layers), built with CUDA. It runs Bend's own device code from the
  packages' bangs; I wrote no CUDA. Its hash is checked on the GPU and on the CPU threads (`+RTS --gpu off -RTS`).
- **The laws.** Where Bend can prove it, a spec the fast code meets (`laws/`). There are ten so far, each with its
  limit stated below.

The workloads import my published BendHub packages at pinned versions (`bend-ml-tensor-array@0.1.16.0`,
`bendtorch@1.1.1.0` and so on), so between two runs only the Bend version changes.

| Workload | What | C target | GPU target |
|---|---|---|---|
| `gemm-tile8` | tensor-array's matrix product, SmolLM2-135M's three feed-forward shapes | yes | tensor-gpu 0.1.4.0 |
| `gemm-fork` | the same products through tensor-fork's parallel blocks | yes (in its blocks) | |
| `matvec-bands` | llama.bend's banded matrix-vector product, SmolLM2-1.7B's shapes | yes | |
| `softmax-ce` | tensor-array's softmax and cross-entropy | yes | |
| `mnist-step` | bend-ml's MNIST training step (784-128-10, batch 100) | yes | |
| `block-step` | BendTorch's SmolLM2-135M block, forward and backward | yes | bendtorch-gpu 1.1.1.0 |
| `attention-step` | the attention half of that block | yes | |
| `rmsnorm-step` | one RMSNorm of that block | yes | bendtorch-gpu 1.1.1.0 |
| `adamw` | BendTorch's AdamW update over 28.3 M weights | yes | |
| `read-native` | a 16 MB weight file read with `File.read_at` | yes | |
| `read-binary` | the same file read with `bend-ml-binary-read` | yes (read-native's) | |
| `softmax-ce-array` | `softmax-ce` on tensor-array 0.1.18.0, which reads each row in place | yes (softmax-ce's) | |
| `mnist-fork` | `mnist-step` with its products through tensor-fork 0.1.5.0 | yes (mnist-step's) | |
| `read-bf16` | two SmolLM2-135M layers read as BF16 from a safetensors file with bendtorch-load | yes | |
| `bpe-encode` | bend-ml-bpe-tokenizer: 256 merges trained, 32,768 words encoded to token ids | yes | |
| `llama-token` | whole tokens of bend-ml-llama's forward pass through the key/value cache, at SmolLM2-135M's widths with 2 layers (since 2026-11-12; not in a run of record yet) | yes | |

Each workload's `README.md` says what it computes, which published package it comes from, how its C target keeps
the same bits, what its oracle hashes and which mutants it must catch.

On my RTX 4050, `gemm-tile8` and `rmsnorm-step` print the CPU's hashes on the GPU, by design: tensor-gpu keeps
tensor-array's order of additions, BendTorch's GPU layers compute each number with the CPU layer's own expression, and
Bend builds the device code without fused multiply-add. `block-step` does not: its losses keep the CPU's bits, but its
final weights differ (`oracles.tsv` has `015f98a384541840` on the GPU, `400cae69095e09cf` on the CPU). On the device
SiLU and attention's softmax take CUDA's float `exp`, which rounds the last bit of some inputs differently from the
host's (BendTorch's own GPU tests show it). The GPU hash repeats from run to run and with CUDA 12.9 and 13.4, so it is
the GPU target's own oracle, and the same binary with `--gpu off` must still print the CPU's.

`repros/` has the minimal cases cut from the workloads, the kind of program an upstream issue can carry.

## Running it

Needs Linux with `perf` and `taskset`, clang, Python 3, and the Bend versions to compare.

```sh
./run.sh                                     # every workload, Bend 2.0.35-2.0.40, 5 rounds, into results/<today>/
ROUNDS=3 VERSIONS="38 39" WORKLOADS="softmax-ce" THREADS="1 16" ./run.sh
BEND_39=~/.bend/bin/bend VERSIONS=39 ./run.sh  # point a version at a binary installed elsewhere
GPU=1 VERSIONS=39 ./run.sh                   # the GPU targets too, into gpu.tsv (needs CUDA and an NVIDIA GPU)
./release.sh 2.0.40                          # a new release against the one before it
```

- `read-binary` and `read-bf16` do not build on 2.0.35 (their package's C effect does not compile against that
  runtime); every other workload builds on 2.0.35-2.0.39.
- `run.sh` builds each workload with each Bend version and its C target, then runs rounds in a fresh seeded order.
  It writes one line per run to `runs.tsv`, the machine's state to `env.tsv`, and a `summary.md` (from `analyze.py`)
  that marks what moved beyond noise (more than 3x the larger spread between rounds) and any output that differs.
- A run checks that each version really ran the thread count it was asked for.
- `GPU=1` adds the GPU targets, built with CUDA by each version and run in the same rounds. Each one is timed twice
  per round: the whole run by the wall clock, then the time its kernels took on the device, from `nsys profile
  --trace=cuda` (`NSYS=0` skips that run). They go to `gpu.tsv`, never `runs.tsv`, and `summary.md` gets a table of
  them. The toolkit is the first of `CUDA_HOME`, `~/.local/cuda12`, `CUDA_PATH`, `/usr/local/cuda` and `/opt/cuda` with
  `nvrtc.h`; a build that does not link libnvrtc (a CPU-only build) counts as a failure. `GPU=1 ./release.sh` passes
  it on.
- `release.sh <version>` builds that release and the one before it from their tags (in a clone of bendlang/bend under
  `build/`, or `$BEND_SRC`), runs the corpus on both at 1 and 16 threads, and prints what changed. On 2.0.39 it took
  2m13s and found that release's change by itself. It needs `bun` too, and stops if the tag is not upstream yet.
  At the end it compares every hash of the run with `oracles.tsv` (`scripts/oracle_diff.py`) and exits 1 if any case
  failed or printed another output. `./release.sh --previous 2.0.40` prints the release it would compare against;
  `ROUNDS=1 OUT=build/rehearsal ./release.sh 2.0.39` rehearses the whole day, bits only.

On the day a release ships (2.0.40, say), on an idle machine:

```sh
./release.sh 2.0.40                                         # into results/<today>-2.0.40/
python3 -I scripts/chart.py 40 results/<today>-2.0.40       # docs/results-2.0.40.svg, from that run
```

The numbers in `results/` come from one machine: a Core Ultra 7 155H, one thread pinned to CPU 3 (a P-core), on mains
power in the `performance` profile, the machine idle unless the result says otherwise. Instructions repeat between
rounds to a few hundred in billions; cycles move by a few percent.

## Reading a run

A run's folder (`results/<date>/`, or `OUT`) holds the raw lines (`runs.tsv`, `gpu.tsv`, `builds.tsv`, `env.tsv`;
`docs/format.md` has every column) and `summary.md`, the file to read first. From the top:

- **A busy mark.** If `scripts/preflight.sh` found the machine busy (load, battery, power profile, other compilers or
  agents, CPU 3's sibling), the first line says so: the bits still count, the timings are a diagnosis, not a result.
- **The main table**, one row per workload and Bend version, one thread: the medians of user-mode instructions
  (`Minstr`) and cycles (`Mcycles`) over the rounds, each with its spread (max - min over the median), the wall time,
  and the change against the newest version in the run. A change in **bold** is beyond noise: more than 3x the larger
  spread of the two versions, with floors of 0.1% for instructions and 1% for cycles, from 3 rounds up. Instructions
  repeat between rounds almost exactly, so they show a compiler change first; cycles are what the change costs on this
  core, and move by a few percent. The last column is the output's hash.
- **Against the C targets**: the newest version's medians over the C target's, in instructions, cycles and wall time.
  1.33x in cycles means Bend's program takes 1.33 times the cycles of the handwritten C for the same bits; "same
  output" must say yes.
- **Threads** (with `THREADS="1 16"`): the wall-time speedup at each thread count over one thread. Every thread count
  must print the same bytes.
- **GPU targets** (with `GPU=1`): wall time and the kernels' time on the device, and whether the GPU prints the CPU's
  bytes. `block-step` does not, by design; its row says so, as its `block-step:gpu` oracle records.
- **Machine**: `env.tsv`'s state (CPU, kernel, pinned CPU and PMU, power, governor, load at start and end).
- **Beyond noise or differing outputs**: every bold change, and every hash that differs from the newest version's,
  between rounds, between thread counts, or from its C or GPU target. "None." is a run where nothing moved.

`oracles.txt` then compares every case with `oracles.tsv`; a line there is a finding to explain in `NOTES.md`, and
`out-<workload>-<version>-t<threads>.txt` keeps the output of one run of each case, to read what changed.

## On another machine

The scripts were written on one machine (a Core Ultra 7 155H on Linux) and say where they depend on it:

- **perf events.** `scripts/pmu.sh` picks the PMU: `cpu_core` (and `cpu_atom` for runs on more threads) on a hybrid
  Intel CPU, plain `cpu` elsewhere (AMD, older Intel); `env.tsv` records it (`pmu`). `perf_event_paranoid` must be at
  most 1 (`sudo sysctl kernel.perf_event_paranoid=1`), since the kernel-mode counts are read too. In a virtual machine
  or a CI runner the counters are often missing: `make check` and `make test` need none.
- **The pinned CPU.** One-thread runs are pinned to CPU 3, a P-core here; `CPU=<n> ./run.sh` picks another (a fast
  core whose SMT sibling is idle; the preflight samples that sibling, `pre_cpu<n>_sibling`). The probes take the same
  `CPU`. `probes/l3/` also needs E-cores that share the L3, so it runs on a hybrid Intel CPU only.
- **Where each Bend version is.** `run.sh` looks for version `<n>` at `build/bin/<n>` (`release.sh`'s source builds),
  then in `BEND_<n>` (dots as underscores: `BEND_39`, `BEND_2_1_0`), then at the paths where my machine keeps each
  release (`~/.bend-2.0.39/bin/bend` and so on, `bend_path` in `run.sh`). On another machine set `BEND_<n>` for each
  version, or build them with `release.sh`. Every version must report the release it names, or the run stops.
- **The rest.** `env.tsv` reads mains power from `/sys/class/power_supply/ADP1` and the power profile from
  `powerprofilesctl`; both say `unknown` where they are missing, and the preflight checks every `Mains` supply.
  `GPU=1` needs CUDA (`CUDA_HOME`) and an NVIDIA GPU.

## The release watch

Between my runs on an idle machine, GitHub's runners watch Bend's releases. Once a day,
`.github/workflows/track.yml` looks for a release of bendlang/bend after the last one it compared. On one, it builds
that release and the one before it from source and counts every workload with both under Cachegrind
(`scripts/track.sh`; one job a workload, both Bends in the same job). Cachegrind's counts repeat exactly from run to
run, so a small move is a real one. A workload is a finding when its instructions move beyond 0.1%, its simulated L1
data misses beyond 5%, or its output is not its oracle; a regression or a changed output opens an issue here. The
counts are kept on the `data` branch (`track/`, `docs/format.md`).

```sh
scripts/count.sh v2.0.40 bpe-encode       # one workload, one Bend: instructions, simulated misses, the hash
scripts/track.sh v2.0.39 v2.0.40 adamw    # two Bends on some workloads (every workload with none), then the verdict
```

Replayed on 2.0.39 against 2.0.40, it flags `bpe-encode` alone as a regression (instructions +9.42%, D1 misses 2.03x)
and 12 workloads as improvements, every output its oracle. Its limits: the caches are simulated (no prefetcher, so
misses move on another scale than the hardware's; the same `bpe-encode` change is 5.6x in perf's L1 misses), it runs
one thread and no GPU, and it counts the binaries the runner's clang builds, so its numbers compare two Bends on one
runner and never stand next to the perf counts of `results/`. Cycles, 16 threads and the GPU stay with `release.sh`
on an idle machine.

### Bisect

A regression or a changed output is then bisected. `scripts/bisect.sh` runs `git bisect` over bendlang/bend's
commits between the two releases; each step builds Bend from source at that commit and counts the workload once
under Cachegrind, and a commit is bad when its count is nearer the new release's than the old one's. The report names
the first bad commit and its pull request, gives Cachegrind's counts per function at that commit and at its parent,
and diffs the C the two Bends emit for the workload, by definition. The release watch runs it on GitHub's runners
(`.github/workflows/bisect.yml`), keeps the report in `track/regressions/` on the `data` branch, and names the commit in
the issue it opens; it posts nothing on bendlang/bend.

```sh
scripts/bisect.sh bpe-encode v2.0.39 v2.0.40 ir   # instructions; d1 for the simulated D1 misses, bits for the output
```

Replayed on `bpe-encode` from 2.0.39 to 2.0.40, it finds both causes of that regression by itself, over 118 commits:
bendlang/bend#1978 for the instructions (+7.84% at that commit; `span_fade` the function that moved, and the C of
`span_fade` and `ctr_take` the definitions that changed) in 7 steps, and #2036 for the simulated D1 misses (2.03x, in
the workload's `bump_go` and the runtime's `rfc_wrap`) in 6 more, both in one job of 1 h 56 min on a runner. On
`gemm-fork`, the drop to 0.26x the instructions from 2.0.32 to 2.0.33 is #1155 (4 steps over 24 commits, 6 minutes).
The three reports are in `track/regressions/` on the `data` branch.

## The history

The same counts, back to Bend 2.0.32: `.github/workflows/history.yml` counts every workload on every release from
2.0.32 to 2.0.40 under Cachegrind, one job a workload with every release counted one after another in it
(`scripts/history.sh`), so each line comes from one runner and one clang. Thirteen workloads build from 2.0.32 on;
`read-bf16` and `read-binary` from 2.0.36, since binary-read's C effect does not match the effect interface before it.
Before 2.0.32 the older checker cannot check the published packages' proofs, so only `read-native` builds there; the
history starts at 2.0.32, and the workloads are not adapted to older releases. All 127 counts print their oracle: no
release from 2.0.32 on changed a bit of any workload's output.

| release | fewer instructions | more | unchanged | biggest moves |
|---|---:|---:|---:|---|
| 2.0.33 | 4 | 0 | 9 | `gemm-fork` 0.26x, `block-step` 0.29x, `mnist-fork` 0.30x, `attention-step` 0.33x |
| 2.0.34 | 0 | 0 | 13 | - |
| 2.0.35 | 3 | 0 | 10 | `attention-step` -1.92%, `block-step` -0.61%, `rmsnorm-step` -0.47% |
| 2.0.36 | 4 | 2 | 7 | `bpe-encode` -7.98%, `rmsnorm-step` -6.73%, `softmax-ce` -1.92%; `read-bf16` and `read-binary` build |
| 2.0.37 | 0 | 3 | 12 | `bpe-encode` +0.42%, `softmax-ce` +0.31%, `mnist-step` +0.14% |
| 2.0.38 | 1 | 2 | 12 | `read-bf16` -2.16%, `softmax-ce` +1.83%, `bpe-encode` +0.12% |
| 2.0.39 | 3 | 0 | 12 | `softmax-ce` 0.41x, `mnist-step` -28.18%, `mnist-fork` -2.36% |
| 2.0.40 | 12 | 1 | 2 | `read-bf16` -22.47%, `mnist-fork` -10.61%, `bpe-encode` +9.42% (and 2.03x the D1 misses) |

A move is one beyond 0.1% in instructions or 5% in simulated D1 misses, as the release watch counts it. From 2.0.32 to
2.0.40 the four workloads that split their work into parallel blocks run about a quarter of the instructions on one
thread (0.26-0.31x), `softmax-ce` 0.40x, `mnist-step` 34% fewer, `rmsnorm-step` 16% fewer and `read-bf16` 24% fewer
than on 2.0.36; `bpe-encode` ends 1.2% above 2.0.32 (2.0.36's 8% given back by 2.0.40), and the two other file reads
do not move. The counts are the runner's (clang 18), not this machine's, so they differ from `results/`' perf counts
(2.0.39's `softmax-ce` is 59% fewer instructions here, 65% with perf on my machine). The run that counted them,
`history/2026-11-07-v2.0.32-v2.0.40/` on the `data` branch, also counted 2.0.39 and 2.0.40 as the release watch's
replay had on another runner: 28 of the 30 counts are the same to the instruction, and `read-bf16`'s two differ by
403 instructions each (0.0003%). Cycles on my machine, measured on an idle machine on 2026-11-08 with 2.0.35 in the
same rounds (`scripts/history_cycles.sh`, `results/2026-11-08-2.0.32-2.0.34/`), say the same as the counts: on 2.0.32
the four parallel-block workloads take 2.6-3.3x 2.0.35's cycles on one thread (+163% to +227%), and 2.0.33 and 2.0.34
are within 3% of it, with the same outputs on all four releases; `rmsnorm-step` is the exception, 13-14% more cycles on
2.0.32-2.0.34 for 0.5% fewer instructions. On 16 threads 2.0.35 is also faster than 2.0.33 and 2.0.34 on
`attention-step` and `block-step` (0.24 against 0.33 s, 0.34 against 0.44-0.45 s), which one-thread counts cannot show.
`read-bf16` and `read-binary` do not build before 2.0.36.

```sh
scripts/history.sh adamw $(scripts/history.sh --releases v2.0.32 v2.0.40)   # one workload on every release
python3 -I scripts/history_report.py <folder>    # steps.tsv, coverage.tsv, report.md from its counts.tsv and gaps.tsv
python3 -I scripts/history_chart.py <folder>     # docs/history.svg
```

## Checks

```sh
make setup     # Bend 2.0.40 (checked by SHA256), then clang and Python 3 checked
make check     # every workload on 1 and 16 threads and every C target, against oracles.tsv
make check-gpu # every GPU target on the GPU and with --gpu off on 1 and 16 threads; skips if there is no GPU
make test      # analyze.py, scripts/chart.py, oracle_diff.py, run.sh's guard and PMU choice, the GPU lane's skip, release.sh on a fake upstream, count.sh, track_verdict.py, bisect.sh and the history's scripts on fakes
make laws      # the ten laws (with --verdict) and their 22 mutants, each refused
make mutate    # break the corpus and the tools on purpose; every mutant must be caught
```

`oracles.tsv` holds each workload's hash, as `run.sh` records it, from a run where every version and every C target
printed it. CI runs all but `make check-gpu` on every push, bits only (GitHub's runners cannot count with `perf`, and
have no GPU). `make check-gpu` is local: with no toolkit or no GPU it says why and passes. `make mutate` has 79
mutants: 73 caught, and 6 that survive with their reason written next to them (five compute the same bits, one changes
what no run reaches). The three block workloads print a hash of their final weights and AdamW moments after the
losses, so one rounding changed inside a layer (SiLU's, say) is caught even when every loss keeps its bits.

## What it has found

On Bend 2.0.35-2.0.40 (`NOTES.md` has each finding with its date and result folder):

- **2.0.40** (`results/2026-11-06-2.0.40/`, the same bits on all 81 cases) runs fewer instructions than 2.0.39 on 12
  of the 15 workloads: `rmsnorm-step` 29.4% fewer (30.2% fewer cycles), `read-bf16` 40.5% (17.2%),
  `softmax-ce-array` 8.5%, `mnist-fork` 5.9%, `adamw` 5.8%; on the GPU, `block-step`'s kernels take 12.9% less device
  time. `read-binary` is unchanged and `gemm-fork` runs 0.9% more instructions (its cycles within noise). One
  regression: `bpe-encode` runs 9.3% more instructions and 28.9% more cycles, the same tokens. I traced it to two
  changes upstream, each confirmed by building 2.0.40 with it undone: bendlang/bend#1978 makes every take of a shared
  node a call on the host (the instructions, bendlang/bend#2081), and bendlang/bend#2036 gives the program 5.6x the L1
  misses (most of the cycles, bendlang/bend#2082).
- **bendlang/bend#1781 on the CPU**: 2.0.40's `Array.get_unchecked` (bendlang/bend#1880) skips the index mask, and
  with it the probe's matrix product runs at 1.04x C's cycles (1.30x with checked reads) and its dot product at 1.04x
  (1.78x), with the same bits (`probes/1781/`). bend-ml's tensor-fork 0.1.7.0 reads its products' cells with it.
- **2.0.39** runs `softmax-ce` in 64.7% fewer instructions than 2.0.38 and `mnist-step` in 27.1% fewer, with the same
  bits; the other workloads stay within 0.03%. All of it traces to bendlang/bend#1806, whose own benchmarks saw no
  change.
- **Bend / C in cycles**, on 2.0.40: 1.09x `softmax-ce-array`, 1.13x `adamw`, 1.17x `gemm-fork`, 1.21x
  `read-binary`, 1.22x `block-step`, 1.30x `gemm-tile8` and `mnist-fork`, 1.37x `attention-step`, 1.50x `read-bf16`,
  1.84x `mnist-step`, 2.32x `matvec-bands`, 2.50x `rmsnorm-step`, 4.47x `softmax-ce`, 19x `read-native`, and 611x
  `bpe-encode`, whose C target counts the pairs in a table indexed by the two ids (`workloads/bpe-encode/`).
  For the matrix-vector product the main cause is the `and` with the array's mask that every `Array.get` keeps
  (`repros/dot_mask.bend`, bendlang/bend#1781); for `softmax-ce` it is tensor-array walking each row as a list (fixed
  in tensor-array 0.1.17.0, which this corpus measured first).
- **Threads**, on 2.0.40 (`results/2026-11-06-2.0.40/`): every workload gives the same bytes at 1 and 16 threads. At
  16 threads `matvec-bands` runs 4.86x faster, `block-step` 4.66x, `attention-step` 4.06x and `gemm-fork` 2.24x;
  `mnist-fork` gains 1.17x and `mnist-step` 1.10x. `gemm-tile8` (0.98x) is tensor-array's sequential product
  (`gemm-fork` is its parallel twin); `softmax-ce`, `adamw`, `rmsnorm-step` and `bpe-encode` run their loops one
  after another (0.99-1.01x); the three file reads and `softmax-ce-array` get slower (0.69-0.95x).

![Two bar charts. Top: Bend 2.0.40 against handwritten C in CPU cycles, from 1.09x for softmax and cross-entropy over the array, 1.13x for the AdamW step and 1.30x for the matrix product, to 2.32x for the matrix-vector product, 4.47x for softmax and cross-entropy, 19x for the built-in file read and 611x for the BPE tokenizer. Bottom: on 16 threads the matrix-vector product runs 4.86x faster than on one, the transformer block 4.66x, attention 4.06x and the parallel matrix product 2.24x; the others gain little or nothing, and the file reads get slower.](docs/results-2.0.40.svg)

The chart is drawn from the raw runs by `python3 -I scripts/chart.py`.

## The laws and their limits

`laws/check.sh` proves ten laws (with `--verdict` too) and runs 22 mutants, each one changed line that the checker
must refuse. `laws/README.md` explains each in plain language.

- `t8_is_dotr`: tensor-array's eight-wide dot and its scalar dot build the same expression, so the same bits under any
  arithmetic. Limit: a model of the two loops over lists of cells, not the `Array` code.
- `bands_len`, `matvec_l_len`: matrix · vector over bands (matvec-bands) gives exactly one number per row, on
  tensor-array's own code. Limit: it counts the numbers, not which product lands where.
- `fork_cover`: tensor-fork's split visits every row (or column) once, in order. Limit: a model of the split, since
  the real one shares arrays through `@unsafe` code.
- `t8_rows_split`, `t8_blocks`: tensor-fork's row blocks, run one after another, compute tensor-array's sequential
  product on the same arrays, the reason gemm-fork prints gemm-tile8's hashes. Limit: the leaves are the real code and
  the tree a model; parallel versus one after another, the U32 offsets and the packing are not proved, and two of the
  three products split by columns, which only `fork_cover` reaches.
- `t8_cols_cells`, `t8_rows_cells`, `cells_len`, `gemm_t8_cells`: gemm-tile8's product, from tensor-array's entry
  point down, writes n x m cells of C, each (row, column) once, row by row, on tensor-array's own code. Limit: it
  lists the writes; that their U32 indexes land on different cells of C is not proved, nor anything about the values
  or the tree of gemm-fork's blocks.

## Adding a workload

A new `workloads/<name>/main.bend` that imports its packages at pinned versions, builds its inputs with `lib/mb.bend`'s
deterministic values, and prints `lib/mb.bend`'s hash of its whole output. A C target goes next to it as `native.c`,
with `lib/mb.h`'s inputs and hash, and must print the same hash. Its hash goes in `oracles.tsv`, and `make check` must
pass. `run.sh` and `make check` pick up every folder under `workloads/`. A GPU target goes next to it as `gpu.bend`,
importing the GPU lane of the same packages, with a `<name>:gpu` line in `oracles.tsv` (its hash on the device), and
`make check-gpu` must pass. `docs/format.md` has the steps, and the files a run writes; `docs/VERSIONING.md` what a
release number means for old results.

## License

MIT.
