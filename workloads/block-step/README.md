# block-step

One decoder block of SmolLM2-135M trained with AdamW: Residual(RMSNorm, attention) then Residual(RMSNorm, SwiGLU), width
576, 9 query heads and 3 key/value heads of 64, RoPE base 100000, feed-forward 1536, on 8 sequences of 64 positions (512
rows), against a target under mean squared error. Two steps (the first makes the optimizer's buffers), forward,
backward and update. The weights, inputs and targets come from a hash of each number's index, so no files are read.
The largest program in the corpus, where a kernel's speed in a probe meets the code around it, and the one `run.sh`'s
thread guard runs.

## Where it comes from

BendTorch's `demo/smol_block.bend` at v1.1.1, unchanged but for the hub imports and its entry:
`bendtorch@1.1.1.0` (the layers, the training step, AdamW), `bendtorch-fast@1.1.1.0` (the parallel linear layers, up
to 256 blocks a product) and `bend-ml-tensor-array@0.1.14.0`. In BendTorch the same block is checked against a PyTorch
twin.

## The C target

`native.c`, with `lib/bt.h` (BendTorch's layers in C, shared with `attention-step` and `rmsnorm-step`): the same block,
the same 2 steps, in BendTorch's order of operations. A Residual adds x + f(x) and its input gradient as dy + dx_f; a
Fork's input gradients are summed as dx_first + dx_second; the SwiGLU product is silu(gate) * up. One thread.

## The GPU target

`gpu.bend`: `main.bend` with `bendtorch-gpu@1.1.1.0` (over `bend-ml-tensor-gpu` 0.1.2.1) in place of `bendtorch-fast`,
the import line alone changed. Its losses keep the CPU's bits, but its final weights do not: on the device SiLU and
attention's softmax take CUDA's float `exp`, which rounds the last bit of some inputs differently from the host's. The
GPU hash repeats from run to run and with CUDA 12.9 and 13.4, so it is the GPU target's own oracle, and the same
binary with `+RTS --gpu off -RTS` must print the CPU's.

## The oracle

It prints each loss's bits, then one hash of the final weights and both AdamW moments, so a rounding changed inside a
layer shows even when every loss keeps its bits. CPU: `400cae69095e09cf`. GPU (`block-step:gpu`): `015f98a384541840`.

## The mutants (`scripts/mutate.py`)

- twice the weight decay: caught;
- `lib/bt.h`: SiLU as x times the reciprocal instead of x over the sum; SiLU's exp in single precision; SiLU plus 1e-7;
  SiLU giving zeros: all four caught on this workload's C target.
