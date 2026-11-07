# Release watch: v2.0.40 against v2.0.39

Bend v2.0.40 (624dd9f4607c) against v2.0.39 (a3efe8a3801f), every workload counted under Cachegrind on one thread with both versions on one machine (clang 18.1.3, valgrind 3.22.0). A finding is a change in instructions beyond 0.1% or in simulated D1 misses beyond 5%, or an output that is not its oracle.

| workload | instructions | D1 misses | output | verdict |
|---|---:|---:|---|---|
| adamw | -3.08% | +0.00% | its oracle | improvement |
| attention-step | -4.01% | +0.00% | its oracle | improvement |
| block-step | -3.82% | -0.00% | its oracle | improvement |
| bpe-encode | +9.42% | 2.03x | its oracle | regression |
| gemm-fork | -2.65% | +0.00% | its oracle | improvement |
| gemm-tile8 | -2.45% | +0.00% | its oracle | improvement |
| matvec-bands | -1.35% | +0.00% | its oracle | improvement |
| mnist-fork | -10.61% | -0.01% | its oracle | improvement |
| mnist-step | -8.10% | -0.02% | its oracle | improvement |
| read-bf16 | -22.47% | +0.01% | its oracle | improvement |
| read-binary | -0.00% | +0.00% | its oracle | same |
| read-native | +0.00% | -0.00% | its oracle | same |
| rmsnorm-step | -9.25% | +0.00% | its oracle | improvement |
| softmax-ce | -1.33% | -0.00% | its oracle | improvement |
| softmax-ce-array | -4.94% | -0.01% | its oracle | improvement |

13 of 15 workloads moved or changed their output.
- adamw: improvement, instructions -3.08%
- attention-step: improvement, instructions -4.01%
- block-step: improvement, instructions -3.82%
- bpe-encode: regression, instructions +9.42%, D1 misses 2.03x
- gemm-fork: improvement, instructions -2.65%
- gemm-tile8: improvement, instructions -2.45%
- matvec-bands: improvement, instructions -1.35%
- mnist-fork: improvement, instructions -10.61%
- mnist-step: improvement, instructions -8.10%
- read-bf16: improvement, instructions -22.47%
- rmsnorm-step: improvement, instructions -9.25%
- softmax-ce: improvement, instructions -1.33%
- softmax-ce-array: improvement, instructions -4.94%

The counts: `track/runs/2026-11-07-v2.0.39-v2.0.40/` on the `data` branch.
The run: https://github.com/nuxyel/metalbend/actions/runs/42377905816.
