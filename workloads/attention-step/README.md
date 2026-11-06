# attention-step

The attention half of `block-step`'s decoder block alone: RMSNorm, the q/k/v projections, RoPE, grouped-query causal
attention (9 query heads, 3 key/value heads of 64) and the output projection, at SmolLM2-135M's sizes on 512 rows,
trained with AdamW under mean squared error for 4 steps. It separates the attention's cost from the feed-forward's.

## Where it comes from

BendTorch's `demo/smol_block.bend` at v1.1.1, cut to the attention half; everything but the model, the entry and the
final hash is the demo's, unchanged. `bendtorch@1.1.1.0`, `bendtorch-fast@1.1.1.0`, `bend-ml-tensor-array@0.1.14.0`.

## The C target

`native.c`, with `lib/bt.h`: the same layers, weights, inputs and targets, the same 4 steps, in BendTorch's order of
operations; a Fork's input gradients summed as dx_q + (dx_k + dx_v).

## The oracle

It prints each loss's bits, then one hash of the final weights and both AdamW moments: `bb7f7e1c79c25bb7`.

## The mutants (`scripts/mutate.py`)

- one step fewer: caught;
- `lib/bt.h`: the causal mask lets a row see one key fewer: caught;
- `lib/bt.h`: the state's hash leaves out the second moments: caught.
