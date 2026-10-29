# Probe: Array.get_unchecked on the CPU (bendlang/bend#1781)

A probe branch, not part of the corpus: the three loops where the array mask showed (2026-10-25), with their reads
switched to `Array.get_unchecked` (bendlang/bend#1880, on main since a888ef27, not released), each against its C
version and the same bits.

## Builds

- Bend 2.0.39: the released binary, `~/.bend/bin/bend`.
- Bend main 4f99f4c1 (2026-10-28, with #1880): a worktree of bendlang/bend at `origin/main`
  (`~/Repos/Bend2/.night/bend-main-unchecked`, branch `phase1/main-unchecked`), `bun install --frozen-lockfile` in
  `bend2/pack`, run through the wrapper `~/Repos/Bend2/.night/bin/bend-main` (`exec bun <worktree>/bend2/main.ts "$@"`),
  as `release.sh` builds a source version. It prints `bend 2.0.39` (main has not bumped the version).
- C: `clang -std=c11 -O3` (clang 23.1.3), the flags `bend -o` gives clang.

## Variants

dotr (tensor-array's scalar dot) and the dot of `repros/dot_mask_standalone.bend` read the next number of both lines
at every step, so the last step reads one number past each line. At the end of a band (2^20 numbers) or of x (2^11),
or of the probe's arrays (2^16), that index is the capacity: `Array.get` wraps it to 0, and `Array.get_unchecked` must
not be given it. So the unchecked loops change shape first, with the same sums in the same order:

| Name | What |
|---|---|
| `checked` | as published (`dot_checked.bend` is `repros/dot_mask_standalone.bend`; the workloads as they are) |
| `km1` | checked reads; k - 1 steps that read the next numbers, then the last product in the `0n` case |
| `last` | checked reads; a third case (`1n`) adds the last product (first run only: it costs more, below) |
| `u` / `km1_unchecked` | `km1` with the unchecked reads (in range, the contract kept) |
| `u0` / `dot_unchecked` | the published shape with the unchecked reads: one read past each line, outside the contract, only to show the mask alone on the same loop |

Tile8's `t8_dot` keeps its shape: its read past the last cell of a line stays inside the packed array's capacity for
every shape of gemm-tile8 (n * ceil(k / 8) is never a power of two there), so its unchecked read keeps the contract.
The emitted C of each checked/unchecked pair differs only in the reads (`blk_at(a, i, lgs)` against
`(u32)i << lgs`).

```sh
python3 -I probes/1781/gen.py ~/.bend/lib/<tensor-array 0.1.16.0>/main.bend   # build/p1781/src/{last,km1,u,u0}
# build: (cd <dir> && <bend> main.bend -o build/p1781/<name>); the dot probes from probes/1781/*.bend
cd build/p1781 && ROUNDS=5 ../../probes/1781/count.sh <binaries> > ../../probes/1781/results/<file>.tsv
python3 -I probes/1781/summarize.py probes/1781/results/<file>.tsv
```

`results/2026-10-28-busy-1.tsv` and `-2.tsv`: two runs of 5 rounds each, busy machine (load average 4.7-13), so the
cycles are not a result; the instructions repeat to within 800 in each case, and the cases common to both runs give
the same counts. In run 1, `matvec_last_u-main` and `gemm_last_u-main` are the unchecked reads on the `last` shape.

## Result (instructions, user mode, one thread on CPU 3)

| | dot | matvec-bands (1.7B, 24 tokens) | gemm-tile8 |
|---|---:|---:|---:|
| checked, 2.0.39 | 3,357.29 M (1.67x) | 10,634.62 M (3.26x) | 13,769.19 M (1.70x) |
| checked, main | 3,357.29 M (1.67x) | 10,634.87 M (3.26x) | 13,769.19 M (1.70x) |
| checked, main, `km1` shape | 3,357.25 M (1.67x) | 11,834.73 M (3.63x) | (no change) |
| unchecked, main (`u`) | 1,433.49 M (0.71x) | 9,820.47 M (3.01x) | 10,520.20 M (1.30x) |
| unchecked, main, one read past (`u0`) | 1,008.47 M (0.50x) | 9,407.74 M (2.89x) | (same as `u`) |
| C | 2,014.38 M | 3,258.47 M | 8,121.86 M |

- The `last` shape (run 1) costs more: matvec 20,297.80 M checked and 19,485.61 M unchecked, the dot 3,491.46 M
  checked on main (3,357.25 M on 2.0.39).
- On matvec-bands the unchecked reads remove 1.2-2.0 G of the 7.4 G between Bend and C; the rest is elsewhere in
  the loop.
- Cycles, busy machine, for orientation only: the unchecked dot runs 302-307 M cycles against C's 289-327 M.
