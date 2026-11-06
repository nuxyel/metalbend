# mnist-fork

`mnist-step`'s training step (the 784-128-10 multilayer perceptron of bend-ml's MNIST demo, batch 100, SGD at a
learning rate of 0.1, 200 steps on the same synthetic batches) with its five matrix products through tensor-fork's
parallel blocks, the path BendTorch's fast layers take. The two products by the 784-wide input split into up to 8
blocks (`par 3`); the three small ones stay in one block (`par 0`). Every other operation is tensor-array's. It runs on
1 and 16 threads; on one thread it measures what the fork path costs over the plain step.

## Where it comes from

bend-ml's MNIST step, as in `mnist-step`, over `bend-ml-tensor-fork@0.1.5.0` and `bend-ml-tensor-array@0.1.18.0`
(bend-ml). tensor-fork 0.1.5.0 shares the operands between its blocks with `@unsafe` code instead of cloning them,
which Bend's compiler does not check yet. Helpers from `lib/ta18.bend`.

## The C target

`native.c` includes `mnist-step`'s: tensor-fork's blocks compute each cell with tensor-array's own dot, in the same order,
so the step has the same bits and one C program is the target of both.

## The oracle

It prints the summed loss's bits and the hash of each parameter: `2d83be930d21fb9f`, `mnist-step`'s.

## The mutants (`scripts/mutate.py`)

- one batch fewer: caught;
- the first layer's product in one block (`par 0` for `par 3`): survives, and must here (tensor-fork's blocks give the
  same bits at any depth, the reason this workload prints `mnist-step`'s hashes);
- C: the ReLU's gradient passes zeros (`>=` for `>`), in `mnist-step`'s C, checked against this workload's oracle:
  caught.
