# mnist-step

bend-ml's MNIST training step: a 784-128-10 multilayer perceptron (ReLU, softmax cross entropy) over tensor-array, batch
100, plain SGD at a learning rate of 0.1, 200 steps. The MNIST files are replaced by synthetic batches (pixels and
initial weights from `lib/mb.bend`'s values, labels from a hash of each row's index), so the program reads no files and
every machine computes the same numbers.

## Where it comes from

bend-ml's demo `demos/mnist/fast.bend` at bend-ml v1.7.0, its step (the types and functions of the forward pass,
backward pass and update) copied unchanged, over `bend-ml-tensor-array@0.1.16.0`.

## The C target

`native.c`: the same step on the same batches, in tensor-array's order of operations. Every product is tensor-array's
dot (four rotating sums, then (a0 + a1) + (a2 + a3)); column sums are that dot against ones; the bias is added as
c + b; ReLU is (v < 0 ? 0 : v); the cross entropy is `softmax-ce`'s.

## The oracle

It prints the summed loss's bits and the hash of each parameter: `2d83be930d21fb9f`.

## The mutants (`scripts/mutate.py`)

- one batch fewer: caught;
- C: the ReLU's gradient passes zeros (`>=` for `>`): caught.
