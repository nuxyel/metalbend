# adamw

BendTorch's AdamW update alone, the loop every training step runs over every weight, on a matrix the size of
SmolLM2-135M's embedding (49,152 x 576, 28.3 M weights): 8 steps, each on a fresh gradient. PyTorch's order of
operations; the bias corrections come from b1^t and b2^t carried in F32. A few multiplications and a square root per
weight, over 28.3 M weights and their two moments: the corpus's element-wise workload, bound by memory.

## Where it comes from

`bendtorch@1.1.1.0`'s `Opt.mat` (BendTorch's `adam_l`), over `bend-ml-tensor-array@0.1.14.0` (the version BendTorch
1.1.1 pins).

## The C target

`native.c`: `adam_l` in the same order: m += c1 * (g - m); v = v * b2 + (c2 * g) * g;
w = w * (1 - lr * wd) + (-step * m) / (sqrt(v) / bc2 + eps), with step = lr / (1 - b1^t) and bc2 = sqrt(1 - b2^t); the
square root through libm's double sqrt rounded to F32, as Bend emits it.

## The oracle

It prints the hash of the weights and of both moments: `b80a7888e4fc8673`.

## The mutants (`scripts/mutate.py`)

- the second moment's decay (0.99 for 0.999): caught;
- C: a larger epsilon: caught;
- `lib/mb.h`: the inputs' second multiplier, checked on this workload's C target: caught.
