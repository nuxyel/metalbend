# 2026-11-06-2.0.40: Bend 2.0.39 -> 2.0.40

- Machine: busy (other_processes): a diagnosis, not a result.
- Oracles: oracles: 81 cases, every hash is its oracle.
- Rounds: 5; medians throughout; **bold** is beyond noise.

## Bend 2.0.40 against 2.0.39 (one thread, user mode)

| workload | 2.0.39 Minstr | 2.0.40 Minstr | Δ instr | Δ cycles |
|---|---:|---:|---:|---:|
| adamw | 17869.9 | 16825.5 | **-5.84%** | -4.19% |
| attention-step | 19641.6 | 19289.3 | **-1.79%** | -1.95% |
| block-step | 31673.1 | 31135.0 | **-1.70%** | -0.99% |
| bpe-encode | 177706.5 | 194163.1 | **+9.26%** | **+28.14%** |
| gemm-fork | 13906.9 | 14031.7 | **+0.90%** | +2.91% |
| gemm-tile8 | 13769.2 | 13443.7 | **-2.36%** | -2.89% |
| matvec-bands | 10634.6 | 10361.8 | **-2.57%** | +4.73% |
| mnist-fork | 13395.4 | 12605.0 | **-5.90%** | **-5.65%** |
| mnist-step | 15939.1 | 15611.7 | **-2.05%** | **-3.57%** |
| read-bf16 | 161.6 | 96.1 | **-40.53%** | **-16.75%** |
| read-binary | 21.2 | 21.2 | -0.00% | -0.14% |
| read-native | 600.2 | 587.6 | **-2.10%** | +1.33% |
| rmsnorm-step | 11815.7 | 8339.9 | **-29.42%** | **-30.21%** |
| softmax-ce | 7819.2 | 7590.8 | **-2.92%** | -2.14% |
| softmax-ce-array | 2703.9 | 2475.5 | **-8.45%** | **-6.85%** |

## Bend / C (one thread, user mode)

| workload | 2.0.39 cycles | 2.0.39 instr | 2.0.40 cycles | 2.0.40 instr |
|---|---:|---:|---:|---:|
| adamw | 1.19x | 1.93x | 1.14x | 1.82x |
| attention-step | 1.41x | 2.18x | 1.38x | 2.14x |
| block-step | 1.23x | 2.11x | 1.22x | 2.07x |
| bpe-encode | 475.25x | 645.27x | 608.97x | 705.03x |
| gemm-fork | 1.14x | 1.71x | 1.18x | 1.73x |
| gemm-tile8 | 1.32x | 1.70x | 1.29x | 1.66x |
| matvec-bands | 2.38x | 3.26x | 2.49x | 3.18x |
| mnist-fork | 1.37x | 2.12x | 1.29x | 1.99x |
| mnist-step | 1.92x | 2.52x | 1.85x | 2.47x |
| read-bf16 | 1.81x | 5.81x | 1.51x | 3.45x |
| read-binary | 1.21x | 1.80x | 1.20x | 1.80x |
| read-native | 19.60x | 50.99x | 19.86x | 49.92x |
| rmsnorm-step | 3.62x | 6.74x | 2.52x | 4.76x |
| softmax-ce | 4.57x | 4.88x | 4.47x | 4.74x |
| softmax-ce-array | 1.17x | 1.69x | 1.09x | 1.54x |

## 16 threads over one (wall time)

| workload | 2.0.39 | 2.0.40 |
|---|---:|---:|
| adamw | 1.01x | 1.00x |
| attention-step | 3.65x | 3.93x |
| block-step | 4.07x | 4.74x |
| bpe-encode | 1.01x | 1.00x |
| gemm-fork | 2.14x | 2.23x |
| gemm-tile8 | 1.00x | 0.98x |
| matvec-bands | 4.35x | 5.15x |
| mnist-fork | 1.08x | 1.17x |
| mnist-step | 1.00x | 1.09x |
| read-bf16 | 0.84x | 0.78x |
| read-binary | 0.79x | 0.67x |
| read-native | 0.78x | 0.65x |
| rmsnorm-step | 1.01x | 0.98x |
| softmax-ce | 1.00x | 0.99x |
| softmax-ce-array | 0.98x | 0.96x |

## GPU kernels (ms on the device, nsys)

| workload | 2.0.39 | 2.0.40 | Δ |
|---|---:|---:|---:|
| block-step | 207.5 | 178.3 | **-14.10%** |
| gemm-tile8 | 53.9 | 55.8 | +3.49% |
| rmsnorm-step | 3277.4 | 3096.8 | -5.51% |
