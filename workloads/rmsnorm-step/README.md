# rmsnorm-step

One RMSNorm of `block-step`'s block (512 rows of 576, epsilon 1e-5, its gain starting from ones), trained with AdamW
under mean squared error for 200 steps. A layer with almost no arithmetic: what it measures is the row-wise forward and
backward loops and the training step's machinery around a layer.

## Where it comes from

BendTorch's `demo/smol_block.bend` at v1.1.1, cut to one RMSNorm. `bendtorch@1.1.1.0`, `bendtorch-fast@1.1.1.0`,
`bend-ml-tensor-array@0.1.14.0`.

## The C target

`native.c`, with `lib/bt.h`: forward, the loss, backward (dx is computed and dropped, as the layer computes it) and the
step, for 200 steps, in BendTorch's order of operations.

## The GPU target

`gpu.bend`: `main.bend` with `bendtorch-gpu@1.1.1.0` in place of `bendtorch-fast`, the import line alone changed. It
prints the CPU's hash on the GPU: BendTorch's GPU layers compute each number with the CPU layer's own expression, and
this layer takes no `exp`.

## The oracle

It prints each loss's bits, then one hash of the final weights and both AdamW moments: `37901ab4cff27378`, on the CPU
and on the GPU (`rmsnorm-step:gpu`).

## The mutants (`scripts/mutate.py`)

- one step fewer: caught;
- the state's hash leaves out the second moment: caught;
- `lib/bt.h`: RMSNorm without its epsilon: caught.
