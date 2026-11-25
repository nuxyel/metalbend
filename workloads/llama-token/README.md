# llama-token

Whole tokens of a Llama, as llama.bend generates them: one position after another through bend-ml-llama's forward
pass, with the key/value cache. Each position is RMSNorm, the q, k and v products, RoPE, grouped-query attention over
the positions so far (9 query heads on 3 key/value heads of 64), the output product, the residual, RMSNorm, SwiGLU's
three products, the residual, and at the end the final norm and the tied head. The widths are SmolLM2-135M's; the
model has 2 layers and a vocabulary of 3,072, so that the head is a fifth of a token's products as it is in the 135M
(30 layers, 49,152 tokens). 32 positions, 283 M multiply-adds in the matrix products.

The other workloads time one kernel or one training step. This one times what a token costs with everything
around the products: the lists the package keeps its vectors in, the cache's writes and reads, the norms and the
activations.

## Where it comes from

`bend-ml-llama@0.2.1.1`'s `forward_gen`, the call llama.bend's generation makes for every token, on
`bend-ml-tensor-array@0.1.20.0`'s `Bands`. The weights are `lib/mb.bend`'s values: cell i of a matrix is its seed's
value i times a scale, whatever bands hold it, and a norm's gains are 1 + 0.2 times its seed's values. The band depth
is llama.bend's rule for the thread count (`depth_for`: one band up to two threads, 16 above), so one thread runs
what llama.bend runs on one thread; the bits are the same on any count.

## The C target

`native.c`: the same weights at the same cells, the same 32 tokens, and the package's order of operations: tensor-
array's dot for every product (four sums that rotate, then (a0 + a1) + (a2 + a3)), RMSNorm's squares added as a
balanced tree, a softmax that subtracts the maximum and adds from the left, SiLU as x / (1 + exp(-x)), and Bend's math
calls (`exp`, `cos`, `sin`, `pow` and `sqrt` in double, rounded to float). It keeps every vector in an array where the
package keeps a list, so the ratio to it says how far a token is from C, lists included.

## The oracle

It prints the hash of every position's logits, 32 lines; the hash of that output is `0a85f2fce42dcde7`.

## The mutants (`scripts/mutate.py`)

- one position fewer: caught;
- the second layer's seeds one apart from the first's instead of sixteen: caught;
- C: the keys and the values swapped in a head's attention: caught;
- C: a query head reads the next key/value head's cache: caught;
- C: attention one key short (the position's own key left out): caught;
- C: RoPE's sine term added instead of subtracted: caught;
- C: SiLU with exp(x) in place of exp(-x): caught;
- C: RMSNorm's squares added from the left instead of as a tree: caught;
- C: a softmax that does not subtract the maximum: caught;
- C: the operands of the residual's addition swapped: survives, and must (IEEE 754 addition is commutative, bit for
  bit).
