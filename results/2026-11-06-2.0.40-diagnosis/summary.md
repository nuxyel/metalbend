# 2026-11-06-2.0.40

**A busy run** (other_processes): its timings are a diagnosis, not a result, and do not go in results/ or a README.

Rounds per pair: 5. Changes are against Bend 2.0.40; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| adamw | 2.0.39 | 17869.9 | 0.00% | 3678.7 | 1.69% | 0.857 | **+6.21%** | +4.37% | b80a7888e4fc8673 |
| adamw | 2.0.40 | 16825.5 | 0.00% | 3524.6 | 0.67% | 0.813 |  |  | b80a7888e4fc8673 |
| attention-step | 2.0.39 | 19641.6 | 0.00% | 3824.8 | 0.43% | 0.854 | **+1.83%** | +1.99% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.40 | 19289.3 | 0.00% | 3750.2 | 0.62% | 0.834 |  |  | bb7f7e1c79c25bb7 |
| block-step | 2.0.39 | 31673.1 | 0.00% | 6150.8 | 0.19% | 1.370 | **+1.73%** | +1.00% | 400cae69095e09cf |
| block-step | 2.0.40 | 31135.0 | 0.00% | 6089.7 | 0.41% | 1.359 |  |  | 400cae69095e09cf |
| bpe-encode | 2.0.39 | 177706.5 | 0.00% | 33712.2 | 5.50% | 7.367 | **-8.48%** | **-21.96%** | 770398c19951fa8c |
| bpe-encode | 2.0.40 | 194163.1 | 0.00% | 43197.6 | 3.45% | 9.438 |  |  | 770398c19951fa8c |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2559.9 | 0.39% | 0.573 | **-0.89%** | -2.83% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.40 | 14031.7 | 0.00% | 2634.4 | 0.32% | 0.590 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3013.8 | 1.21% | 0.670 | **+2.42%** | +2.97% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.40 | 13443.7 | 0.00% | 2926.8 | 0.66% | 0.651 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2447.8 | 10.90% | 0.542 | **+2.63%** | -4.52% | ff8b18c16b517923 |
| matvec-bands | 2.0.40 | 10361.8 | 0.00% | 2563.6 | 15.17% | 0.571 |  |  | ff8b18c16b517923 |
| mnist-fork | 2.0.39 | 13395.4 | 0.00% | 2432.6 | 0.98% | 0.542 | **+6.27%** | **+5.99%** | 2d83be930d21fb9f |
| mnist-fork | 2.0.40 | 12605.0 | 0.00% | 2295.1 | 0.79% | 0.511 |  |  | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3398.5 | 1.15% | 0.753 | **+2.10%** | **+3.70%** | 2d83be930d21fb9f |
| mnist-step | 2.0.40 | 15611.7 | 0.00% | 3277.3 | 0.86% | 0.726 |  |  | 2d83be930d21fb9f |
| read-bf16 | 2.0.39 | 161.6 | 0.00% | 59.1 | 1.36% | 0.027 | **+68.16%** | **+20.12%** | d09cf49a5e86a7f6 |
| read-bf16 | 2.0.40 | 96.1 | 0.00% | 49.2 | 2.23% | 0.025 |  |  | d09cf49a5e86a7f6 |
| read-binary | 2.0.39 | 21.2 | 0.00% | 20.7 | 0.30% | 0.016 | +0.00% | +0.14% | 9b44f947a6f6c6b9 |
| read-binary | 2.0.40 | 21.2 | 0.00% | 20.7 | 0.72% | 0.016 |  |  | 9b44f947a6f6c6b9 |
| read-native | 2.0.39 | 600.2 | 0.00% | 337.0 | 8.64% | 0.087 | **+2.14%** | -1.31% | 9b44f947a6f6c6b9 |
| read-native | 2.0.40 | 587.6 | 0.00% | 341.5 | 1.54% | 0.089 |  |  | 9b44f947a6f6c6b9 |
| rmsnorm-step | 2.0.39 | 11815.7 | 0.00% | 2331.5 | 0.54% | 0.519 | **+41.68%** | **+43.29%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.40 | 8339.9 | 0.00% | 1627.2 | 0.70% | 0.364 |  |  | 37901ab4cff27378 |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2295.0 | 0.78% | 0.507 | **+3.01%** | +2.19% | debeda8b7bc50c1f |
| softmax-ce | 2.0.40 | 7590.8 | 0.00% | 2245.8 | 0.79% | 0.497 |  |  | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.39 | 2703.9 | 0.00% | 592.6 | 1.03% | 0.142 | **+9.23%** | **+7.36%** | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.40 | 2475.5 | 0.00% | 552.0 | 1.11% | 0.133 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.40 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| adamw | 9244.0 | 3099.7 | 0.715 | 1.82x | 1.14x | 1.14x | yes |
| attention-step | 9017.6 | 2710.1 | 0.608 | 2.14x | 1.38x | 1.37x | yes |
| block-step | 15014.4 | 4998.8 | 1.118 | 2.07x | 1.22x | 1.21x | yes |
| bpe-encode | 275.4 | 70.9 | 0.025 | 705.03x | 608.97x | 385.22x | yes |
| gemm-fork | 8117.3 | 2240.7 | 0.501 | 1.73x | 1.18x | 1.18x | yes |
| gemm-tile8 | 8121.9 | 2277.0 | 0.508 | 1.66x | 1.29x | 1.28x | yes |
| matvec-bands | 3258.5 | 1029.7 | 0.242 | 3.18x | 2.49x | 2.36x | yes |
| mnist-fork | 6326.0 | 1773.0 | 0.407 | 1.99x | 1.29x | 1.25x | yes |
| mnist-step | 6326.0 | 1774.1 | 0.409 | 2.47x | 1.85x | 1.78x | yes |
| read-bf16 | 27.8 | 32.7 | 0.021 | 3.45x | 1.51x | 1.21x | yes |
| read-binary | 11.8 | 17.2 | 0.015 | 1.80x | 1.20x | 1.11x | yes |
| read-native | 11.8 | 17.2 | 0.015 | 49.92x | 19.86x | 6.08x | yes |
| rmsnorm-step | 1752.4 | 644.7 | 0.147 | 4.76x | 2.52x | 2.48x | yes |
| softmax-ce | 1603.0 | 502.2 | 0.121 | 4.74x | 4.47x | 4.10x | yes |
| softmax-ce-array | 1603.0 | 505.5 | 0.122 | 1.54x | 1.09x | 1.09x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| adamw | 2.0.39 | 0.857 | 0.850 | 1.01x | yes |
| adamw | 2.0.40 | 0.813 | 0.811 | 1.00x | yes |
| attention-step | 2.0.39 | 0.854 | 0.234 | 3.65x | yes |
| attention-step | 2.0.40 | 0.834 | 0.212 | 3.93x | yes |
| block-step | 2.0.39 | 1.370 | 0.337 | 4.07x | yes |
| block-step | 2.0.40 | 1.359 | 0.287 | 4.74x | yes |
| bpe-encode | 2.0.39 | 7.367 | 7.304 | 1.01x | yes |
| bpe-encode | 2.0.40 | 9.438 | 9.399 | 1.00x | yes |
| gemm-fork | 2.0.39 | 0.573 | 0.268 | 2.14x | yes |
| gemm-fork | 2.0.40 | 0.590 | 0.265 | 2.23x | yes |
| gemm-tile8 | 2.0.39 | 0.670 | 0.671 | 1.00x | yes |
| gemm-tile8 | 2.0.40 | 0.651 | 0.662 | 0.98x | yes |
| matvec-bands | 2.0.39 | 0.542 | 0.125 | 4.35x | yes |
| matvec-bands | 2.0.40 | 0.571 | 0.111 | 5.15x | yes |
| mnist-fork | 2.0.39 | 0.542 | 0.502 | 1.08x | yes |
| mnist-fork | 2.0.40 | 0.511 | 0.438 | 1.17x | yes |
| mnist-step | 2.0.39 | 0.753 | 0.750 | 1.00x | yes |
| mnist-step | 2.0.40 | 0.726 | 0.665 | 1.09x | yes |
| read-bf16 | 2.0.39 | 0.027 | 0.032 | 0.84x | yes |
| read-bf16 | 2.0.40 | 0.025 | 0.032 | 0.78x | yes |
| read-binary | 2.0.39 | 0.016 | 0.021 | 0.79x | yes |
| read-binary | 2.0.40 | 0.016 | 0.025 | 0.67x | yes |
| read-native | 2.0.39 | 0.087 | 0.112 | 0.78x | yes |
| read-native | 2.0.40 | 0.089 | 0.137 | 0.65x | yes |
| rmsnorm-step | 2.0.39 | 0.519 | 0.516 | 1.01x | yes |
| rmsnorm-step | 2.0.40 | 0.364 | 0.373 | 0.98x | yes |
| softmax-ce | 2.0.39 | 0.507 | 0.508 | 1.00x | yes |
| softmax-ce | 2.0.40 | 0.497 | 0.499 | 0.99x | yes |
| softmax-ce-array | 2.0.39 | 0.142 | 0.145 | 0.98x | yes |
| softmax-ce-array | 2.0.40 | 0.133 | 0.139 | 0.96x | yes |

## GPU targets (medians: the whole run's wall time, and its kernels' time on the device from nsys)

| workload | bend | s | spread | kernel ms | spread | kernels | hash | same output as the CPU |
|---|---|---:|---:|---:|---:|---:|---|---|
| block-step | 2.0.39 | 1.266 | 157.50% | 207.5 | 3.76% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| block-step | 2.0.40 | 3.209 | 65.88% | 178.3 | 3.09% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| gemm-tile8 | 2.0.39 | 2.371 | 88.13% | 53.9 | 10.06% | 120 | 0c6d7fee9a7ddf37 | yes |
| gemm-tile8 | 2.0.40 | 2.362 | 90.20% | 55.8 | 10.33% | 120 | 0c6d7fee9a7ddf37 | yes |
| rmsnorm-step | 2.0.39 | 5.898 | 37.92% | 3277.4 | 2.04% | 5000 | 37901ab4cff27378 | yes |
| rmsnorm-step | 2.0.40 | 5.714 | 35.88% | 3096.8 | 2.07% | 5000 | 37901ab4cff27378 | yes |

## Machine (env.tsv)

| key | value |
|---|---|
| cpu | Intel(R) Core(TM) Ultra 7 155H |
| kernel | 7.2.8-9-omarchy |
| cpu_pinned | 3 |
| pmu | cpu_core (one thread); cpu_core cpu_atom (more) |
| ac_online | unknown |
| power_profile | performance |
| governor | powersave |
| no_turbo | 0 |
| thp | always |
| loadavg_start | 1.10 1.13 0.79 |
| loadavg_end | 1.06 1.28 1.16 |
| pre_other_processes | claude x2 |
| pre_cpu3_sibling | cpu4 0% |
| pre_perf_event_paranoid | 1 |
| busy | other_processes |

## Beyond noise or differing outputs

- adamw: 2.0.39 instructions +6.21% against 2.0.40 (noise 0.10%)
- attention-step: 2.0.39 instructions +1.83% against 2.0.40 (noise 0.10%)
- block-step: 2.0.39 instructions +1.73% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 instructions -8.48% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 cycles -21.96% against 2.0.40 (noise 5.50%)
- gemm-fork: 2.0.39 instructions -0.89% against 2.0.40 (noise 0.10%)
- gemm-tile8: 2.0.39 instructions +2.42% against 2.0.40 (noise 0.10%)
- matvec-bands: 2.0.39 instructions +2.63% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 instructions +6.27% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 cycles +5.99% against 2.0.40 (noise 1.00%)
- mnist-step: 2.0.39 instructions +2.10% against 2.0.40 (noise 0.10%)
- mnist-step: 2.0.39 cycles +3.70% against 2.0.40 (noise 1.15%)
- read-bf16: 2.0.39 instructions +68.16% against 2.0.40 (noise 0.10%)
- read-bf16: 2.0.39 cycles +20.12% against 2.0.40 (noise 2.23%)
- read-native: 2.0.39 instructions +2.14% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 instructions +41.68% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 cycles +43.29% against 2.0.40 (noise 1.00%)
- softmax-ce: 2.0.39 instructions +3.01% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 instructions +9.23% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 cycles +7.36% against 2.0.40 (noise 1.11%)
