// mnist-fork's target: mnist-step's C, unchanged. tensor-fork's blocks compute each product's cells with
// tensor-array's own code, in the same order, so the training step has the same bits and one C program is the target
// of both; on one thread it measures what the shared-operand fork path costs over the plain step.
#include "../mnist-step/native.c"
