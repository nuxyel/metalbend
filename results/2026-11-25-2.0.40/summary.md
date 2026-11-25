# 2026-11-25-2.0.40

Rounds per pair: 5. Changes are against Bend 2.0.40; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| adamw | 2.0.39 | 17869.9 | 0.00% | 3661.0 | 1.06% | 0.847 | **+6.21%** | +3.84% | b80a7888e4fc8673 |
| adamw | 2.0.40 | 16825.5 | 0.00% | 3525.6 | 1.95% | 0.810 |  |  | b80a7888e4fc8673 |
| attention-step | 2.0.39 | 19641.6 | 0.00% | 3830.0 | 0.28% | 0.853 | **+1.83%** | +2.37% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.40 | 19289.3 | 0.00% | 3741.5 | 0.38% | 0.833 |  |  | bb7f7e1c79c25bb7 |
| block-step | 2.0.39 | 31673.1 | 0.00% | 6154.4 | 0.75% | 1.370 | **+1.73%** | +0.99% | 400cae69095e09cf |
| block-step | 2.0.40 | 31135.0 | 0.00% | 6094.1 | 0.55% | 1.359 |  |  | 400cae69095e09cf |
| bpe-encode | 2.0.39 | 177706.5 | 0.00% | 33501.6 | 0.42% | 7.318 | **-8.48%** | **-22.17%** | 770398c19951fa8c |
| bpe-encode | 2.0.40 | 194163.1 | 0.00% | 43044.0 | 0.72% | 9.371 |  |  | 770398c19951fa8c |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2553.5 | 0.69% | 0.572 | **-0.89%** | -2.85% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.40 | 14031.7 | 0.00% | 2628.4 | 0.44% | 0.589 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3018.8 | 0.87% | 0.671 | **+2.42%** | +3.18% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.40 | 13443.7 | 0.00% | 2925.9 | 1.46% | 0.650 |  |  | 0c6d7fee9a7ddf37 |
| llama-token | 2.0.39 | 3506.5 | 0.00% | 850.0 | 10.30% | 0.199 | **+6.85%** | +2.35% | 0a85f2fce42dcde7 |
| llama-token | 2.0.40 | 3281.6 | 0.00% | 830.5 | 6.69% | 0.192 |  |  | 0a85f2fce42dcde7 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2486.7 | 10.74% | 0.550 | **+2.63%** | +2.50% | ff8b18c16b517923 |
| matvec-bands | 2.0.40 | 10361.8 | 0.00% | 2426.0 | 5.86% | 0.538 |  |  | ff8b18c16b517923 |
| mnist-fork | 2.0.39 | 13395.4 | 0.00% | 2435.0 | 1.06% | 0.541 | **+6.27%** | **+5.54%** | 2d83be930d21fb9f |
| mnist-fork | 2.0.40 | 12605.0 | 0.00% | 2307.2 | 1.23% | 0.516 |  |  | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3388.3 | 1.99% | 0.751 | **+2.10%** | +3.55% | 2d83be930d21fb9f |
| mnist-step | 2.0.40 | 15611.6 | 0.00% | 3272.0 | 0.78% | 0.728 |  |  | 2d83be930d21fb9f |
| read-bf16 | 2.0.39 | 161.6 | 0.00% | 59.3 | 18.93% | 0.028 | **+68.16%** | +20.08% | d09cf49a5e86a7f6 |
| read-bf16 | 2.0.40 | 96.1 | 0.00% | 49.4 | 2.33% | 0.025 |  |  | d09cf49a5e86a7f6 |
| read-binary | 2.0.39 | 21.2 | 0.00% | 20.7 | 2.28% | 0.016 | +0.00% | -0.03% | 9b44f947a6f6c6b9 |
| read-binary | 2.0.40 | 21.2 | 0.00% | 20.7 | 1.05% | 0.017 |  |  | 9b44f947a6f6c6b9 |
| read-native | 2.0.39 | 600.2 | 0.00% | 336.0 | 5.03% | 0.086 | **+2.14%** | -1.95% | 9b44f947a6f6c6b9 |
| read-native | 2.0.40 | 587.6 | 0.00% | 342.7 | 0.99% | 0.087 |  |  | 9b44f947a6f6c6b9 |
| rmsnorm-step | 2.0.39 | 11815.6 | 0.00% | 2334.9 | 0.31% | 0.520 | **+41.68%** | **+43.45%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.40 | 8339.9 | 0.00% | 1627.7 | 0.72% | 0.366 |  |  | 37901ab4cff27378 |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2281.8 | 1.46% | 0.511 | **+3.01%** | +1.43% | debeda8b7bc50c1f |
| softmax-ce | 2.0.40 | 7590.7 | 0.00% | 2249.7 | 2.58% | 0.500 |  |  | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.39 | 2703.9 | 0.00% | 593.5 | 1.64% | 0.143 | **+9.23%** | **+7.49%** | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.40 | 2475.4 | 0.00% | 552.2 | 2.28% | 0.135 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.40 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| adamw | 9244.0 | 3081.1 | 0.717 | 1.82x | 1.14x | 1.13x | yes |
| attention-step | 9017.5 | 2721.6 | 0.611 | 2.14x | 1.37x | 1.36x | yes |
| block-step | 15014.4 | 4996.2 | 1.123 | 2.07x | 1.22x | 1.21x | yes |
| bpe-encode | 275.4 | 70.7 | 0.024 | 705.05x | 608.46x | 388.85x | yes |
| gemm-fork | 8117.3 | 2250.1 | 0.502 | 1.73x | 1.17x | 1.17x | yes |
| gemm-tile8 | 8121.9 | 2285.7 | 0.515 | 1.66x | 1.28x | 1.26x | yes |
| llama-token | 1144.7 | 498.5 | 0.121 | 2.87x | 1.67x | 1.58x | yes |
| matvec-bands | 3258.5 | 1030.7 | 0.243 | 3.18x | 2.35x | 2.22x | yes |
| mnist-fork | 6326.0 | 1773.2 | 0.408 | 1.99x | 1.30x | 1.26x | yes |
| mnist-step | 6326.0 | 1774.2 | 0.409 | 2.47x | 1.84x | 1.78x | yes |
| read-bf16 | 27.8 | 32.9 | 0.020 | 3.46x | 1.50x | 1.27x | yes |
| read-binary | 11.8 | 17.2 | 0.015 | 1.80x | 1.20x | 1.11x | yes |
| read-native | 11.8 | 17.2 | 0.015 | 49.96x | 19.90x | 5.72x | yes |
| rmsnorm-step | 1752.4 | 648.8 | 0.148 | 4.76x | 2.51x | 2.47x | yes |
| softmax-ce | 1603.0 | 505.2 | 0.122 | 4.74x | 4.45x | 4.09x | yes |
| softmax-ce-array | 1603.0 | 504.1 | 0.121 | 1.54x | 1.10x | 1.11x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| adamw | 2.0.39 | 0.847 | 0.848 | 1.00x | yes |
| adamw | 2.0.40 | 0.810 | 0.810 | 1.00x | yes |
| attention-step | 2.0.39 | 0.853 | 0.239 | 3.57x | yes |
| attention-step | 2.0.40 | 0.833 | 0.209 | 3.98x | yes |
| block-step | 2.0.39 | 1.370 | 0.334 | 4.10x | yes |
| block-step | 2.0.40 | 1.359 | 0.289 | 4.71x | yes |
| bpe-encode | 2.0.39 | 7.318 | 7.301 | 1.00x | yes |
| bpe-encode | 2.0.40 | 9.371 | 9.392 | 1.00x | yes |
| gemm-fork | 2.0.39 | 0.572 | 0.281 | 2.04x | yes |
| gemm-fork | 2.0.40 | 0.589 | 0.263 | 2.24x | yes |
| gemm-tile8 | 2.0.39 | 0.671 | 0.682 | 0.98x | yes |
| gemm-tile8 | 2.0.40 | 0.650 | 0.663 | 0.98x | yes |
| llama-token | 2.0.39 | 0.199 | 0.113 | 1.77x | yes |
| llama-token | 2.0.40 | 0.192 | 0.109 | 1.77x | yes |
| matvec-bands | 2.0.39 | 0.550 | 0.126 | 4.36x | yes |
| matvec-bands | 2.0.40 | 0.538 | 0.112 | 4.81x | yes |
| mnist-fork | 2.0.39 | 0.541 | 0.491 | 1.10x | yes |
| mnist-fork | 2.0.40 | 0.516 | 0.434 | 1.19x | yes |
| mnist-step | 2.0.39 | 0.751 | 0.718 | 1.05x | yes |
| mnist-step | 2.0.40 | 0.728 | 0.660 | 1.10x | yes |
| read-bf16 | 2.0.39 | 0.028 | 0.043 | 0.66x | yes |
| read-bf16 | 2.0.40 | 0.025 | 0.033 | 0.77x | yes |
| read-binary | 2.0.39 | 0.016 | 0.021 | 0.78x | yes |
| read-binary | 2.0.40 | 0.017 | 0.024 | 0.69x | yes |
| read-native | 2.0.39 | 0.086 | 0.128 | 0.67x | yes |
| read-native | 2.0.40 | 0.087 | 0.126 | 0.69x | yes |
| rmsnorm-step | 2.0.39 | 0.520 | 0.522 | 1.00x | yes |
| rmsnorm-step | 2.0.40 | 0.366 | 0.369 | 0.99x | yes |
| softmax-ce | 2.0.39 | 0.511 | 0.516 | 0.99x | yes |
| softmax-ce | 2.0.40 | 0.500 | 0.501 | 1.00x | yes |
| softmax-ce-array | 2.0.39 | 0.143 | 0.147 | 0.97x | yes |
| softmax-ce-array | 2.0.40 | 0.135 | 0.138 | 0.98x | yes |

## GPU targets (medians: the whole run's wall time, and its kernels' time on the device from nsys)

| workload | bend | s | spread | kernel ms | spread | kernels | hash | same output as the CPU |
|---|---|---:|---:|---:|---:|---:|---|---|
| block-step | 2.0.39 | 1.266 | 170.28% | 206.5 | 4.88% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| block-step | 2.0.40 | 3.200 | 62.28% | 177.2 | 2.25% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| gemm-tile8 | 2.0.39 | 0.432 | 486.46% | 52.8 | 4.52% | 120 | 0c6d7fee9a7ddf37 | yes |
| gemm-tile8 | 2.0.40 | 0.417 | 481.33% | 54.1 | 9.38% | 120 | 0c6d7fee9a7ddf37 | yes |
| rmsnorm-step | 2.0.39 | 5.959 | 36.92% | 3293.2 | 1.16% | 5000 | 37901ab4cff27378 | yes |
| rmsnorm-step | 2.0.40 | 7.633 | 26.70% | 3099.8 | 1.22% | 5000 | 37901ab4cff27378 | yes |

## Machine (env.tsv)

| key | value |
|---|---|
| cpu | Intel(R) Core(TM) Ultra 7 155H |
| kernel | 7.2.8-9-omarchy |
| cpu_pinned | 3 |
| pmu | cpu_core (one thread); cpu_core cpu_atom (more) |
| ac_online | 1 |
| power_profile | performance |
| governor | powersave |
| no_turbo | 0 |
| thp | always |
| loadavg_start | 0.82 0.33 0.82 |
| loadavg_end | 1.30 1.70 1.41 |
| pre_other_processes | claude x1, agents idle 0.0% |
| pre_cpu3_sibling | cpu4 0% |
| pre_perf_event_paranoid | 1 |
| busy | no |

## Beyond noise or differing outputs

- adamw: 2.0.39 instructions +6.21% against 2.0.40 (noise 0.10%)
- attention-step: 2.0.39 instructions +1.83% against 2.0.40 (noise 0.10%)
- block-step: 2.0.39 instructions +1.73% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 instructions -8.48% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 cycles -22.17% against 2.0.40 (noise 1.00%)
- gemm-fork: 2.0.39 instructions -0.89% against 2.0.40 (noise 0.10%)
- gemm-tile8: 2.0.39 instructions +2.42% against 2.0.40 (noise 0.10%)
- llama-token: 2.0.39 instructions +6.85% against 2.0.40 (noise 0.10%)
- matvec-bands: 2.0.39 instructions +2.63% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 instructions +6.27% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 cycles +5.54% against 2.0.40 (noise 1.23%)
- mnist-step: 2.0.39 instructions +2.10% against 2.0.40 (noise 0.10%)
- read-bf16: 2.0.39 instructions +68.16% against 2.0.40 (noise 0.10%)
- read-native: 2.0.39 instructions +2.14% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 instructions +41.68% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 cycles +43.45% against 2.0.40 (noise 1.00%)
- softmax-ce: 2.0.39 instructions +3.01% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 instructions +9.23% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 cycles +7.49% against 2.0.40 (noise 2.28%)
