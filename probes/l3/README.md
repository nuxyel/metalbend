# Probe: does a busy L3 move Bend's cycle ratio against C?

A probe, not part of the corpus. On 2026-10-27 (NOTES) gemm-fork's Bend against gemm-tile8's plain C came out 0.94x
in cycles on a busy machine and 1.13x in a second run, and the plain C's cycles moved most with the load. The guess
was that the plain order leans on the L3, shared with whatever else runs, where the blocked loops sit in L2. This
probe busies the L3 on purpose and measures the ratios with and without it.

## What it runs

- The measured programs, one thread on CPU 3 (`taskset -c 3`), Bend 2.0.39: `gemm-fork` and `gemm-tile8` as `run.sh`
  builds them, and their C targets (`clang -std=c11 -O3`): `gemm-fork-c` (tensor-fork's blocks) and `gemm-tile8-c`
  (the plain order). All four print the oracle hash `0c6d7fee9a7ddf37`.
- Counters: `perf stat -e cpu_core/instructions/u,cpu_core/cycles/u,cpu_core/mem_load_retired.l3_miss/u` (the P-core
  PMU, user mode).
- The antagonist, `stream.c`: one process per E-core that shares the P-cores' L3, each pinned with `taskset`, adding 1
  to every word of its own 64 MB buffer until `SIGTERM`, then printing its rate. On the Core Ultra 7 155H those are
  CPUs 12-19 (`/sys/devices/cpu_atom/cpus` is 12-21; 20-21, the low-power E-cores, have no L3 and are left out).
  Eight of them stream about 67 GB/s together.
- Rounds: odd rounds run `idle` then `busy`, even rounds the other way; within a condition the four binaries run in
  an order shuffled with the round as seed. The antagonists start 2 s before a `busy` condition and stop after it.

```sh
scripts/preflight.sh
ROUNDS=5 probes/l3/run.sh $(probes/l3/build.sh) > probes/l3/results/<file>.tsv     # all eight E-cores
STREAMS=2 ROUNDS=5 probes/l3/run.sh $(probes/l3/build.sh) > probes/l3/results/<file>.tsv
python3 -I probes/l3/summarize.py probes/l3/results/<file>.tsv
```

`build.sh [<bend>] [<tag>]` takes another compiler (default `~/.bend-2.0.39/bin/bend`, tag `39`).

## Results (2026-11-01, idle machine)

Preflight before each block: load 0.60-1.28, mains, `performance`, CPU 3's sibling at 0-1%; the only other processes
were two idle `claude` and `codex` sessions (under 3% of a CPU). The load averages in the files during and after a
`busy` condition are the antagonists' own. Every run printed the oracle hash; instructions repeat to within 2,400.

`results/2026-11-01-1.tsv` and `-2.tsv` (eight streams), `-streams1.tsv` and `-streams2.tsv`: 5 rounds each.
Bend / C in cycles, the median of the per-round ratios (the range over the rounds):

| pair | idle | 8 streams | 2 streams | 1 stream |
|---|---:|---:|---:|---:|
| gemm-fork / its blocked C | 1.139-1.141 | 1.130-1.132 (-0.8%) | 1.133 (-0.5%) | 1.131 (-0.2%) |
| gemm-fork / gemm-tile8's plain C (the old pairing) | 1.130-1.138 | 1.006-1.018 (-10 to -12%; single rounds 0.994-1.102) | 1.138 (+0.2%) | 1.131 (0%) |
| gemm-tile8 / its plain C | 1.336-1.338 | 1.241-1.263 (-5.5 to -7%) | 1.320 (-1%) | 1.337 (0%) |

Cycles, busy / idle, with eight streams (both blocks): gemm-fork 1.09-1.10x, its C 1.10x, gemm-tile8 1.14x,
gemm-tile8's C 1.21-1.23x (and its spread over the rounds grows to 4-10%). With one or two streams every program
gains 1.5-3%. Idle, all four miss the L3 almost never (under 0.04 M times); with eight streams the misses are
0.21-0.22 M (gemm-fork), 1.28 M (its C), 2.6 M (gemm-tile8) and 1.2-1.3 M (gemm-tile8's C).

- The guess holds in direction: a saturated L3 and memory bus slow the plain C most, so ratios against the plain C
  fall by 6-12%; the blocked pair, which slows alike in Bend and C, moves under 1%. gemm-tile8's Bend misses the L3
  twice as often as its C under load and still slows less.
- It does not reach 0.94x: the old pairing's lowest round here is 0.994. The rest of 10-27's gap came from something
  this probe does not reproduce (that machine ran compilers on the P-cores at load 5-10).
- One or two streams (about 35 GB/s with two) leave every ratio within 1%; it takes most of the E-cores streaming
  to move them.
