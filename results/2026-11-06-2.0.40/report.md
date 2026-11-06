# 2026-11-06-2.0.40: Bend 2.0.39 -> 2.0.40

- Machine: idle by the preflight.
- Oracles: oracles: 81 cases, every hash is its oracle.
- Rounds: 5; medians throughout; **bold** is beyond noise.

## Bend 2.0.40 against 2.0.39 (one thread, user mode)

| workload | 2.0.39 Minstr | 2.0.40 Minstr | Δ instr | Δ cycles |
|---|---:|---:|---:|---:|
| adamw | 17869.9 | 16825.5 | **-5.84%** | **-4.23%** |
| attention-step | 19641.6 | 19289.3 | **-1.79%** | -2.33% |
| block-step | 31673.1 | 31135.0 | **-1.70%** | -0.63% |
| bpe-encode | 177706.5 | 194163.1 | **+9.26%** | **+28.89%** |
| gemm-fork | 13906.9 | 14031.7 | **+0.90%** | +2.97% |
| gemm-tile8 | 13769.2 | 13443.7 | **-2.36%** | **-3.22%** |
| matvec-bands | 10634.6 | 10361.8 | **-2.57%** | -2.01% |
| mnist-fork | 13395.4 | 12605.0 | **-5.90%** | **-5.55%** |
| mnist-step | 15939.1 | 15611.7 | **-2.05%** | **-3.17%** |
| read-bf16 | 161.6 | 96.1 | **-40.53%** | **-17.15%** |
| read-binary | 21.2 | 21.2 | -0.00% | +0.10% |
| read-native | 600.2 | 587.6 | **-2.10%** | -1.35% |
| rmsnorm-step | 11815.6 | 8339.9 | **-29.42%** | **-30.22%** |
| softmax-ce | 7819.2 | 7590.7 | **-2.92%** | -1.89% |
| softmax-ce-array | 2703.9 | 2475.4 | **-8.45%** | **-7.75%** |

## Bend / C (one thread, user mode)

| workload | 2.0.39 cycles | 2.0.39 instr | 2.0.40 cycles | 2.0.40 instr |
|---|---:|---:|---:|---:|
| adamw | 1.18x | 1.93x | 1.13x | 1.82x |
| attention-step | 1.40x | 2.18x | 1.37x | 2.14x |
| block-step | 1.23x | 2.11x | 1.22x | 2.07x |
| bpe-encode | 474.24x | 645.29x | 611.26x | 705.05x |
| gemm-fork | 1.14x | 1.71x | 1.17x | 1.73x |
| gemm-tile8 | 1.34x | 1.70x | 1.30x | 1.66x |
| matvec-bands | 2.37x | 3.26x | 2.32x | 3.18x |
| mnist-fork | 1.37x | 2.12x | 1.30x | 1.99x |
| mnist-step | 1.90x | 2.52x | 1.84x | 2.47x |
| read-bf16 | 1.80x | 5.81x | 1.50x | 3.46x |
| read-binary | 1.20x | 1.80x | 1.21x | 1.80x |
| read-native | 19.64x | 51.03x | 19.38x | 49.96x |
| rmsnorm-step | 3.59x | 6.74x | 2.50x | 4.76x |
| softmax-ce | 4.55x | 4.88x | 4.47x | 4.74x |
| softmax-ce-array | 1.18x | 1.69x | 1.09x | 1.54x |

## 16 threads over one (wall time)

| workload | 2.0.39 | 2.0.40 |
|---|---:|---:|
| adamw | 1.00x | 1.00x |
| attention-step | 3.52x | 4.06x |
| block-step | 4.08x | 4.66x |
| bpe-encode | 1.00x | 1.00x |
| gemm-fork | 2.05x | 2.24x |
| gemm-tile8 | 0.99x | 0.98x |
| matvec-bands | 4.33x | 4.86x |
| mnist-fork | 1.11x | 1.17x |
| mnist-step | 1.02x | 1.10x |
| read-bf16 | 0.78x | 0.95x |
| read-binary | 0.76x | 0.74x |
| read-native | 0.55x | 0.69x |
| rmsnorm-step | 1.00x | 0.99x |
| softmax-ce | 0.99x | 1.01x |
| softmax-ce-array | 0.99x | 0.95x |

## GPU kernels (ms on the device, nsys)

| workload | 2.0.39 | 2.0.40 | Δ |
|---|---:|---:|---:|
| block-step | 205.9 | 179.3 | **-12.93%** |
| gemm-tile8 | 55.2 | 55.6 | +0.70% |
| rmsnorm-step | 3277.7 | 3118.6 | -4.85% |
