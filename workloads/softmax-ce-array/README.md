# softmax-ce-array

`softmax-ce`'s program on a newer tensor-array: the same 6 rounds of fresh logits over SmolLM2's vocabulary (64 rows of
49,152), the same labels, the same loss and gradient. tensor-array 0.1.17.0 changed how the softmax cross entropy
reaches each row (it reads the row of the `Array` in place instead of walking it as a list), so the two workloads time
the old and the new path of one computation, and must print the same bits.

## Where it comes from

`bend-ml-tensor-array@0.1.18.0`'s `Mat.softmax_ce` (bend-ml), the version that carries the change `softmax-ce` measured
first (`repros/softmax_array.bend`). Its helpers (random matrices, the hash of a matrix) are `lib/ta18.bend`, since a
`Mat` of one tensor-array version is not one of another.

## The C target

`native.c` includes `softmax-ce`'s: 0.1.18.0 computes the same numbers in the same order as 0.1.16.0, so one C program is
the target of both.

## The oracle

It prints each round's loss bits and the hash of the gradients' sum: `debeda8b7bc50c1f`, `softmax-ce`'s.

## The mutants (`scripts/mutate.py`)

- the first round's seed: caught;
- C: exp in single precision (`expf`), in `softmax-ce`'s C, checked against this workload's oracle: caught.
