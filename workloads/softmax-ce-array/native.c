// softmax-ce-array's target: softmax-ce's C, unchanged. tensor-array 0.1.18.0 computes the same softmax cross entropy
// in the same order as 0.1.16.0 (only how it reaches each row changed), so one C program is the target of both.
#include "../softmax-ce/native.c"
