# Bend v2.0.32 to v2.0.40 on the corpus

Every workload counted under Cachegrind (one thread, the simulated caches of `scripts/count.sh`) with each release, a workload's releases all on one machine (clang 18.1.3, valgrind 3.22.0). A step is a finding when instructions move beyond 0.1% or simulated D1 misses beyond 5%, or the output is not its oracle.

| release | faster | slower | mixed | same | first counted | not built | output changed | biggest moves (instructions) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v2.0.33 | 4 | 0 | 0 | 9 | 0 | 2 | 0 | gemm-fork 0.26x, block-step 0.29x, mnist-fork 0.30x |
| v2.0.34 | 0 | 0 | 0 | 13 | 0 | 2 | 0 | - |
| v2.0.35 | 3 | 0 | 0 | 10 | 0 | 2 | 0 | attention-step -1.92%, block-step -0.61%, rmsnorm-step -0.47% |
| v2.0.36 | 4 | 2 | 0 | 7 | 2 | 0 | 0 | bpe-encode -7.98%, rmsnorm-step -6.73%, softmax-ce -1.92% |
| v2.0.37 | 0 | 3 | 0 | 12 | 0 | 0 | 0 | bpe-encode +0.42%, softmax-ce +0.31%, mnist-step +0.14% |
| v2.0.38 | 1 | 2 | 0 | 12 | 0 | 0 | 0 | read-bf16 -2.16%, softmax-ce +1.83%, bpe-encode +0.12% |
| v2.0.39 | 3 | 0 | 0 | 12 | 0 | 0 | 0 | softmax-ce 0.41x, mnist-step -28.18%, mnist-fork -2.36% |
| v2.0.40 | 12 | 1 | 0 | 2 | 0 | 0 | 0 | read-bf16 -22.47%, mnist-fork -10.61%, bpe-encode +9.42% |

From each workload's first release to v2.0.40, instructions:

| workload | from | instructions there | instructions on the last | change |
|---|---|---:|---:|---:|
| gemm-fork | v2.0.32 | 50,696,482,359 | 12,997,404,596 | 0.26x |
| mnist-fork | v2.0.32 | 45,306,184,516 | 11,811,254,192 | 0.26x |
| block-step | v2.0.32 | 106,543,213,098 | 29,241,368,729 | 0.27x |
| attention-step | v2.0.32 | 58,142,141,513 | 18,159,060,910 | 0.31x |
| softmax-ce | v2.0.32 | 21,582,890,811 | 8,720,332,041 | 0.40x |
| mnist-step | v2.0.32 | 22,631,518,237 | 14,872,802,625 | -34.28% |
| read-bf16 | v2.0.36 | 152,198,896 | 115,432,507 | -24.16% |
| rmsnorm-step | v2.0.32 | 12,529,741,851 | 10,556,120,532 | -15.75% |
| softmax-ce-array | v2.0.32 | 2,760,507,175 | 2,624,200,757 | -4.94% |
| adamw | v2.0.32 | 17,416,913,756 | 16,880,053,789 | -3.08% |
| gemm-tile8 | v2.0.32 | 13,206,576,414 | 12,882,479,697 | -2.45% |
| matvec-bands | v2.0.32 | 10,239,991,222 | 10,102,158,281 | -1.35% |
| read-native | v2.0.32 | 629,676,812 | 629,690,199 | +0.00% |
| read-binary | v2.0.36 | 37,050,771 | 37,059,456 | +0.02% |
| bpe-encode | v2.0.32 | 211,567,434,995 | 214,161,062,646 | +1.23% |

Not counted (the workload does not build or run there; recorded, not adapted):

- read-bf16: v2.0.32, v2.0.33, v2.0.34, v2.0.35 (compile-failed: read-bf16.c:14124:12: error: call to undeclared function 'io_res'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]; compile-failed: read-bf16.c:14232:86: error: too few arguments to function call, expected 3, have 2; compile-failed: read-bf16.c:14298:86: error: too few arguments to function call, expected 3, have 2)
- read-binary: v2.0.32, v2.0.33, v2.0.34, v2.0.35 (compile-failed: read-binary.c:3510:12: error: call to undeclared function 'io_res'; ISO C99 and later do not support implicit function declarations [-Wimplicit-function-declaration]; compile-failed: read-binary.c:3522:76: error: too few arguments to function call, expected 3, have 2; compile-failed: read-binary.c:3588:76: error: too few arguments to function call, expected 3, have 2)
