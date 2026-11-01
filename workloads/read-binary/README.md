# read-binary

`read-native`'s 16 MB of F32 (`data/dense.bin`), read into an `Array` with `bend-ml-binary-read`: a C library effect
that stands in for the dense read Base lacks (bendlang/bend#1573), so the two workloads compare the language's read
with the workaround.

## Where it comes from

`bend-ml-binary-read@0.2.0.0` (bend-ml), a contained workaround kept until Base reads dense files; its `read_f32`
reads the numbers in one call.

## The C target

`native.c` includes `read-native`'s: one `fread` of the file, then the hash. Both workloads do the same work in the same
order, so one C target serves both.

## The oracle

It prints the hash of the numbers: `9b44f947a6f6c6b9`, `read-native`'s.

## The mutants (`scripts/mutate.py`)

- the read starts one cell late: caught.

It builds on Bend 2.0.36 and later; 2.0.35 cannot build it (`results/2026-10-25-f/summary.md`).
