# matvec-bands

SmolLM2-1.7B's feed-forward products at one token, as llama.bend runs them while it decodes: x (2048) goes through up
(8192 x 2048) and then down (2048 x 8192), 24 times, each output the next input. The weights are tensor-array's Bands
(16 bands, a matrix · vector product that never copies the weights); 805 M multiply-adds in all. A product of a matrix
and a vector reads every weight once, so this is the memory-bound side of the corpus, where `gemm-tile8` is the
compute-bound one.

## Where it comes from

`bend-ml-tensor-array@0.1.16.0`'s `Bands` and its scalar dot (`dotr`), the path llama.bend's decoding takes for every
weight product. Each band is filled from its own seed with `lib/mb.bend`'s values.

## The C target

`native.c`: the same weights (each band from its own seed), the same 24 tokens, and tensor-array's scalar dot: each
product goes to the first of four sums and the sums rotate, then (a0 + a1) + (a2 + a3).

## The oracle

It prints the hash of the last x: `ff8b18c16b517923`.

## The mutants (`scripts/mutate.py`)

- one token fewer: caught;
- a band's second child takes the first one's seed: caught;
- C: the four sums joined in another order: caught;
- C: the operands of one addition swapped: survives, and must (IEEE 754 addition is commutative, bit for bit).

`lib/mb.bend`'s and `lib/mb.h`'s hash mutants are checked on this workload too.

## The laws and the repro

`bands_len` and `matvec_l_len`: the product over bands gives exactly one number per row, on tensor-array's own code (it
counts the numbers, not which product lands where). `repros/dot_mask.bend` is the dot cut out of this workload: each
`Array.get` keeps an `and` with the array's mask, which clang cannot remove (bendlang/bend#1781).
