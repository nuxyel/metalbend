# MetalBend

A corpus of real machine-learning workloads for Bend 2's compiler, run on every Bend release. I cut the workloads
from my three Bend projects (bend-ml, llama.bend and BendTorch): matrix products, a banded matrix-vector product,
attention, normalization, an optimizer step, a training step, file reads. Each one is checked by its exact output and
timed by hardware counters, so a release that changes a workload's speed or its bits shows up as a number.

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
./run.sh                                     # every workload, Bend 2.0.35-2.0.39, 5 rounds, into results/<today>/
ROUNDS=3 VERSIONS="38 39" WORKLOADS="softmax-ce" THREADS="1 16" ./run.sh
BEND_39=~/.bend/bin/bend VERSIONS=39 ./run.sh  # point a version at a binary installed elsewhere
GPU=1 VERSIONS=39 ./run.sh                   # the GPU targets too, into gpu.tsv (needs CUDA and an NVIDIA GPU)
./release.sh 2.0.40                          # a new release against the one before it
```

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

## Checks

```sh
make setup     # Bend 2.0.39 (checked by SHA256), then clang and Python 3 checked
make check     # every workload on 1 and 16 threads and every C target, against oracles.tsv
make check-gpu # every GPU target on the GPU and with --gpu off on 1 and 16 threads; skips if there is no GPU
make test      # analyze.py, scripts/chart.py, oracle_diff.py, run.sh's guard, the GPU lane's skip, release.sh on a fake upstream
make laws      # the ten laws (with --verdict) and their 22 mutants, each refused
make mutate    # break the corpus and the tools on purpose; every mutant must be caught
```

`oracles.tsv` holds each workload's hash, as `run.sh` records it, from a run where every version and every C target
printed it. CI runs all but `make check-gpu` on every push, bits only (GitHub's runners cannot count with `perf`, and
have no GPU). `make check-gpu` is local: with no toolkit or no GPU it says why and passes. `make mutate` has 57
mutants: 52 caught, and 5 that survive with their reason written next to them (four compute the same bits, one changes
what no run reaches). The three block workloads print a hash of their final weights and AdamW moments after the
losses, so one rounding changed inside a layer (SiLU's, say) is caught even when every loss keeps its bits.

## What it has found

On Bend 2.0.35-2.0.39 (`NOTES.md` has each finding with its date and result folder):

- **2.0.39** runs `softmax-ce` in 64.7% fewer instructions than 2.0.38 and `mnist-step` in 27.1% fewer, with the same
  bits; the other workloads stay within 0.03%. All of it traces to bendlang/bend#1806, whose own benchmarks saw no
  change.
- **Bend / C in cycles**, on 2.0.39: 1.20x `adamw`, 1.33x `gemm-tile8`, 1.96x `mnist-step`, 2.32x `matvec-bands`,
  4.75x `softmax-ce`, 21x `read-native` (6.1x in wall time). For the matrix-vector product the main cause is the
  `and` with the array's mask that every `Array.get` keeps (`repros/dot_mask.bend`, bendlang/bend#1781); for
  `softmax-ce` it is tensor-array walking each row as a list (fixed in tensor-array 0.1.17.0, which this corpus
  measured first). The other five workloads got their C targets on 2026-10-27 (the same bits); they are measured at
  the next idle run.
- **Threads**, on 2.0.39 (`results/2026-10-25-f/`): every workload gives the same bytes at 1 and 16 threads. At 16
  threads `block-step` runs 4.49x faster, `matvec-bands` 4.21x, `attention-step` 3.67x and `gemm-fork` 2.17x. The
  other seven gain nothing: `gemm-tile8` is tensor-array's sequential product (`gemm-fork` is its parallel twin),
  `mnist-step`, `softmax-ce`, `adamw` and `rmsnorm-step` run their loops one after another (1.00-1.04x), and the two
  file reads get slower (0.83x and 0.90x).

![Two bar charts. Top: Bend 2.0.39 needs 1.20x the CPU cycles of handwritten C for the AdamW step, 1.33x for the matrix product, 1.96x for the MNIST step, 2.32x for the matrix-vector product, 4.75x for softmax and cross-entropy and 21x for the file read. Bottom: on 16 threads the transformer block runs 4.49x faster than on one, the matrix-vector product 4.21x, attention 3.67x and the parallel matrix product 2.17x; the other seven gain nothing (1.00-1.04x) or get slower (the two file reads, 0.90x and 0.83x).](docs/results-2.0.39.svg)

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
