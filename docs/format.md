# The format

What MetalBend 1.x keeps stable: what a workload is, what a run writes, and how a workload and its oracle are added.
A change to anything here that old results cannot follow is a new major version (`docs/VERSIONING.md`).

## A workload

A folder `workloads/<name>/`; `run.sh`, `release.sh` and `make check` pick up every folder there.

| File | Required | What |
|---|---|---|
| `main.bend` | yes | the program, built with `bend main.bend -o <bin>` from inside the folder |
| `native.c` | no | its C target: `clang -std=c11 -O3 native.c -lm`, one thread, the same order of operations and the same bits |
| `gpu.bend` | no | its GPU target: `main.bend` through the GPU lanes of the same packages, built with a CUDA toolkit in `CUDA_HOME` |

Rules for `main.bend`:

- It imports my published BendHub packages at exact versions, and `../../lib/mb.bend` for its inputs and its hash.
- Its inputs are deterministic: `lib/mb.bend`'s values, or `data/` files made by `lib/gen_dense.py` (`make data`).
- It prints its results as text and ends; whatever it prints is its output. It takes no arguments, so a run differs
  only by the Bend version, the thread count and the target.
- Its output must not depend on the thread count. Bend promises the same bits on any number of threads, and the
  corpus checks it.

A C target uses `lib/mb.h` (and `lib/bt.h` for BendTorch's layers) for the same inputs and hash, and prints what
`main.bend` prints, byte for byte. A C target may include its twin's (`gemm-fork` and `read-binary` reuse code
that way) when it does the same work in the same order.

## The oracle

A run's hash is the first 16 hex digits of the SHA-256 of its whole standard output. `oracles.tsv` has one line per
workload (`<name>\t<hash>`), and one per GPU target (`<name>:gpu\t<hash>`, the hash on the device; the same binary
with `+RTS --gpu off -RTS` must print `<name>`'s hash).

- An oracle line is written from a run where every Bend version in the run, at 1 and 16 threads, and the C target
  print the same hash. A GPU target's hash may differ from the CPU's (CUDA's float `exp`, say): then the line holds
  the device's hash, and NOTES says why.
- A different hash is a finding, never noise. `make check` (CPU) and `make check-gpu` (local) compare against
  `oracles.tsv`, and `release.sh` ends with `scripts/oracle_diff.py`, which exits 1 on any difference.
- When a workload's output changes on purpose, both hashes go in `NOTES.md` with the date (`docs/VERSIONING.md`).

## A run: `results/<folder>/`

`run.sh` writes one folder (`OUT`, `results/<date>` by default; `release.sh` uses `results/<date>-<version>`). Every
file is tab-separated with a header line. A 2.0.x version is named by its last number (`39` for 2.0.39), a version
from 2.1 on by its full number (`2.1.0`), the C target by `c`.

`runs.tsv`, one line per CPU run:

| Column | What |
|---|---|
| `round` | the round, from 1; each round runs every case once in an order shuffled with the round as seed |
| `workload` | the folder name |
| `bend` | the version's name (`39`, `2.1.0`), or `c` |
| `instructions`, `cycles` | user-mode counts from `perf stat` (the pinned CPU's PMU, `cpu_core` or plain `cpu`, `scripts/pmu.sh`; on more threads instructions sum every PMU and cycles are not comparable) |
| `kinstructions`, `kcycles` | the kernel-mode counts, kept apart (page faults, huge pages) |
| `seconds` | wall time of the run |
| `hash` | the oracle hash of its output |
| `status` | `ok`, or `exit<code>` |
| `loadavg` | the one-minute load average just before the run |
| `threads` | the thread count asked for; a one-thread run is pinned to CPU 3 (`CPU=<n>` picks another) |

`gpu.tsv` (only with `GPU=1`): `round`, `workload`, `bend`, `seconds` (wall), `kernel_ms` and `kernels` (the device's
kernel time and count from a second run under `nsys`, empty with `NSYS=0`), `hash`, `status`, `loadavg`.

`builds.tsv`: `workload`, `bend` (a version's name, `c` or `gpu-<name>`), `status` (`ok` or `fail`), `seconds`.

`threads.tsv`: `bend`, `threads`, `threads_peak`: the thread guard's check that a version honored the thread count.

`env.tsv`, `key` and `value`: `date`, `cpu`, `kernel`, `clang` (its version; clang is not pinned, so this line is the
record), `ac_online`, `power_profile`, `governor` (the pinned CPU's), `no_turbo`, `thp` (transparent huge pages),
`bun`, `cpu_pinned` (the CPU of the one-thread runs, 3 unless `CPU` says otherwise), `pmu` (the PMUs that counted
them, `scripts/pmu.sh`), `loadavg_start` and `loadavg_end`, `metalbend` (the commit, `-dirty` if the tree had
changes), `bend_<name>` (what each version reports) and `source_<name>` (`source <commit> (<tree>)` for a source
build, `binary sha256:<16 hex>` for a released binary), the `pre_<check>` lines of `scripts/preflight.sh --env`
(`pre_ac`, `pre_power_profile`, `pre_loadavg`, `pre_other_processes`, `pre_perf_event_paranoid`, and
`pre_cpu<n>_sibling` for the pinned CPU, `pre_cpu3_sibling` by default) and `busy` (the checks that failed, or `no`),
one `pkg_<name>@<version>` per BendHub package the corpus imports (its store id and a hash of its files,
`scripts/packages.py`), and with `GPU=1` also `gpu`, `cuda_home` and `nsys`. Runs before 2026-11-01 have no
`cpu_pinned` or `pmu` line; they were pinned to CPU 3 and counted by `cpu_core`.

`oracles.txt`: `scripts/oracle_diff.py`'s comparison of every case with `oracles.tsv`, written at the end of the run
(run.sh exits 1 when it lists a problem).

`out-<workload>-<version>-t<threads>.txt` (and `-gpu.txt`): one run's output, kept for reading a differing hash.

`summary.md`: `analyze.py`'s tables (medians and spreads by workload and version, Bend / C ratios, threads, GPU, the
machine's state from `env.tsv`, with a busy run marked at the top) and what moved beyond noise: more than 3x the
larger spread between rounds, with floors of 0.1% for instructions and 1% for cycles, and only with 3 rounds or more.

A folder's `README.md`, written by hand, says what the run was for and the state of the machine. A run on a busy
machine is a diagnosis, not a result, and its folder does not go in `results/`. `results/` is append-only.

## Adding a workload

1. `workloads/<name>/main.bend`, as above; `native.c` and `gpu.bend` if it has them.
2. Run it on every version it builds on, at 1 and 16 threads, and its C target:
   `ROUNDS=1 THREADS="1 16" WORKLOADS=<name> OUT=build/new ./run.sh`; every hash in `build/new/runs.tsv` must be one.
3. Add `<name>\t<hash>` to `oracles.tsv` (and `<name>:gpu`), keep it sorted, and run `make check` (and
   `make check-gpu`).
4. A line in the README's workload table, a mutant in `scripts/mutate.py` if it has a C target, and a dated entry in
   `NOTES.md`. This is a minor version.
