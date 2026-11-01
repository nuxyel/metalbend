# softmax-ce

The loss of a language model's head: tensor-array's softmax cross entropy over SmolLM2's vocabulary, 64 rows of 49,152
logits, with its gradient. Per row: the max, exp of each logit minus the max, the sum, the divisions, the loss of the
row's label; the F32 work around a model that is not a product. 6 rounds, each on fresh logits (a gradient fed back as
logits would be near zero, and exp near zero is not the work of a real head). The labels come from a hash of each
row's index.

## Where it comes from

`bend-ml-tensor-array@0.1.16.0`'s `Mat.softmax_ce`, the loss bend-ml's MNIST demo and BendTorch train with. That
version walks each row as a list; tensor-array 0.1.17.0 walks it as an array, a change this workload measured first
(`repros/softmax_array.bend`).

## The C target

`native.c`: the same 6 rounds of fresh logits, in the same order of operations: per row the max (x < y ? y : x, from
the first number), exp(h - max) through libm's double exp rounded to F32 (how Bend emits `F32.exp`), one running sum,
the divisions, the loss minus log(max(p[label], 1e-12)), the gradient (p - onehot) / 64; each round's loss divided by
64, the gradients summed.

## The oracle

It prints each round's loss bits and the hash of the gradients' sum: `debeda8b7bc50c1f`.

## The mutants (`scripts/mutate.py`)

- the first round's seed: caught;
- the labels' shift: caught;
- C: exp in single precision (`expf`): caught;
- C: the row's max takes ties from the right: survives, and must here (a tie picks an equal number, and the logits
  hold no -0 or NaN, the only values where the two differ);
- `oracles.tsv`: one digit of this workload's oracle: caught.
