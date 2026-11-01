# 2026-11-01-2.0.39-rehearsal: Bend 2.0.38 -> 2.0.39

- Machine: busy (other_processes): a diagnosis, not a result.
- Oracles: oracles: 81 cases, every hash is its oracle.
- Rounds: 5; medians throughout; **bold** is beyond noise.

## Bend 2.0.39 against 2.0.38 (one thread, user mode)

| workload | 2.0.38 Minstr | 2.0.39 Minstr | Δ instr | Δ cycles |
|---|---:|---:|---:|---:|
| adamw | 17869.9 | 17869.9 | +0.00% | -1.04% |
| attention-step | 19641.6 | 19641.6 | -0.00% | -0.20% |
| block-step | 31673.1 | 31673.1 | +0.00% | +0.43% |
| bpe-encode | 177706.5 | 177706.5 | +0.00% | +0.21% |
| gemm-fork | 13906.9 | 13906.9 | -0.00% | -2.31% |
| gemm-tile8 | 13769.2 | 13769.2 | -0.00% | +2.62% |
| matvec-bands | 10634.6 | 10634.6 | +0.00% | +0.22% |
| mnist-fork | 13780.5 | 13395.4 | **-2.79%** | **-5.04%** |
| mnist-step | 21878.3 | 15939.1 | **-27.15%** | **-23.53%** |
| read-bf16 | 161.6 | 161.6 | -0.02% | -0.03% |
| read-binary | 21.2 | 21.2 | +0.00% | -0.52% |
| read-native | 600.2 | 600.2 | +0.00% | -1.65% |
| rmsnorm-step | 11815.7 | 11815.7 | -0.00% | -1.32% |
| softmax-ce | 22152.4 | 7819.2 | **-64.70%** | **-64.84%** |
| softmax-ce-array | 2703.9 | 2703.9 | -0.00% | -0.07% |

## Bend / C (one thread, user mode)

| workload | 2.0.38 cycles | 2.0.38 instr | 2.0.39 cycles | 2.0.39 instr |
|---|---:|---:|---:|---:|
| adamw | 1.20x | 1.93x | 1.18x | 1.93x |
| attention-step | 1.41x | 2.18x | 1.41x | 2.18x |
| block-step | 1.23x | 2.11x | 1.23x | 2.11x |
| bpe-encode | 461.73x | 645.27x | 462.72x | 645.27x |
| gemm-fork | 1.16x | 1.71x | 1.13x | 1.71x |
| gemm-tile8 | 1.31x | 1.70x | 1.34x | 1.70x |
| matvec-bands | 2.36x | 3.26x | 2.37x | 3.26x |
| mnist-fork | 1.46x | 2.18x | 1.39x | 2.12x |
| mnist-step | 2.50x | 3.46x | 1.91x | 2.52x |
| read-bf16 | 1.80x | 5.81x | 1.80x | 5.81x |
| read-binary | 1.20x | 1.80x | 1.20x | 1.80x |
| read-native | 19.33x | 50.99x | 19.01x | 50.99x |
| rmsnorm-step | 3.67x | 6.74x | 3.62x | 6.74x |
| softmax-ce | 12.83x | 13.82x | 4.51x | 4.88x |
| softmax-ce-array | 1.18x | 1.69x | 1.18x | 1.69x |

## 16 threads over one (wall time)

| workload | 2.0.38 | 2.0.39 |
|---|---:|---:|
| adamw | 1.00x | 0.99x |
| attention-step | 3.57x | 3.59x |
| block-step | 4.10x | 4.08x |
| bpe-encode | 0.99x | 1.00x |
| gemm-fork | 2.16x | 2.12x |
| gemm-tile8 | 1.00x | 0.99x |
| matvec-bands | 4.35x | 4.41x |
| mnist-fork | 1.07x | 1.12x |
| mnist-step | 1.01x | 1.03x |
| read-bf16 | 0.84x | 1.01x |
| read-binary | 0.79x | 0.71x |
| read-native | 0.69x | 0.66x |
| rmsnorm-step | 1.00x | 0.98x |
| softmax-ce | 0.99x | 1.00x |
| softmax-ce-array | 0.97x | 0.94x |

## GPU kernels (ms on the device, nsys)

| workload | 2.0.38 | 2.0.39 | Δ |
|---|---:|---:|---:|
| block-step | 208.9 | 204.6 | -2.07% |
| gemm-tile8 | 53.4 | 54.0 | +1.06% |
| rmsnorm-step | 3273.8 | 3272.3 | -0.05% |
