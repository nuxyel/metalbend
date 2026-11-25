# 2026-11-25-2.0.40: Bend 2.0.39 -> 2.0.40

- Machine: idle by the preflight.
- Oracles: oracles: 86 cases, every hash is its oracle.
- Rounds: 5; medians throughout; **bold** is beyond noise.

## Bend 2.0.40 against 2.0.39 (one thread, user mode)

| workload | 2.0.39 Minstr | 2.0.40 Minstr | Δ instr | Δ cycles |
|---|---:|---:|---:|---:|
| adamw | 17869.9 | 16825.5 | **-5.84%** | -3.70% |
| attention-step | 19641.6 | 19289.3 | **-1.79%** | -2.31% |
| block-step | 31673.1 | 31135.0 | **-1.70%** | -0.98% |
| bpe-encode | 177706.5 | 194163.1 | **+9.26%** | **+28.48%** |
| gemm-fork | 13906.9 | 14031.7 | **+0.90%** | +2.93% |
| gemm-tile8 | 13769.2 | 13443.7 | **-2.36%** | -3.08% |
| llama-token | 3506.5 | 3281.6 | **-6.41%** | -2.29% |
| matvec-bands | 10634.6 | 10361.8 | **-2.57%** | -2.44% |
| mnist-fork | 13395.4 | 12605.0 | **-5.90%** | **-5.25%** |
| mnist-step | 15939.1 | 15611.6 | **-2.05%** | -3.43% |
| read-bf16 | 161.6 | 96.1 | **-40.53%** | -16.72% |
| read-binary | 21.2 | 21.2 | -0.00% | +0.03% |
| read-native | 600.2 | 587.6 | **-2.10%** | +1.99% |
| rmsnorm-step | 11815.6 | 8339.9 | **-29.42%** | **-30.29%** |
| softmax-ce | 7819.2 | 7590.7 | **-2.92%** | -1.41% |
| softmax-ce-array | 2703.9 | 2475.4 | **-8.45%** | **-6.97%** |

## Bend / C (one thread, user mode)

| workload | 2.0.39 cycles | 2.0.39 instr | 2.0.40 cycles | 2.0.40 instr |
|---|---:|---:|---:|---:|
| adamw | 1.19x | 1.93x | 1.14x | 1.82x |
| attention-step | 1.41x | 2.18x | 1.37x | 2.14x |
| block-step | 1.23x | 2.11x | 1.22x | 2.07x |
| bpe-encode | 473.57x | 645.29x | 608.46x | 705.05x |
| gemm-fork | 1.13x | 1.71x | 1.17x | 1.73x |
| gemm-tile8 | 1.32x | 1.70x | 1.28x | 1.66x |
| llama-token | 1.70x | 3.06x | 1.67x | 2.87x |
| matvec-bands | 2.41x | 3.26x | 2.35x | 3.18x |
| mnist-fork | 1.37x | 2.12x | 1.30x | 1.99x |
| mnist-step | 1.91x | 2.52x | 1.84x | 2.47x |
| read-bf16 | 1.80x | 5.81x | 1.50x | 3.46x |
| read-binary | 1.20x | 1.80x | 1.20x | 1.80x |
| read-native | 19.52x | 51.03x | 19.90x | 49.96x |
| rmsnorm-step | 3.60x | 6.74x | 2.51x | 4.76x |
| softmax-ce | 4.52x | 4.88x | 4.45x | 4.74x |
| softmax-ce-array | 1.18x | 1.69x | 1.10x | 1.54x |

## 16 threads over one (wall time)

| workload | 2.0.39 | 2.0.40 |
|---|---:|---:|
| adamw | 1.00x | 1.00x |
| attention-step | 3.57x | 3.98x |
| block-step | 4.10x | 4.71x |
| bpe-encode | 1.00x | 1.00x |
| gemm-fork | 2.04x | 2.24x |
| gemm-tile8 | 0.98x | 0.98x |
| llama-token | 1.77x | 1.77x |
| matvec-bands | 4.36x | 4.81x |
| mnist-fork | 1.10x | 1.19x |
| mnist-step | 1.05x | 1.10x |
| read-bf16 | 0.66x | 0.77x |
| read-binary | 0.78x | 0.69x |
| read-native | 0.67x | 0.69x |
| rmsnorm-step | 1.00x | 0.99x |
| softmax-ce | 0.99x | 1.00x |
| softmax-ce-array | 0.97x | 0.98x |

## GPU kernels (ms on the device, nsys)

| workload | 2.0.39 | 2.0.40 | Δ |
|---|---:|---:|---:|
| block-step | 206.5 | 177.2 | -14.23% |
| gemm-tile8 | 52.8 | 54.1 | +2.44% |
| rmsnorm-step | 3293.2 | 3099.8 | **-5.87%** |
