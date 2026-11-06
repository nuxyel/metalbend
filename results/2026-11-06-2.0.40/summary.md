# 2026-11-06-2.0.40

Rounds per pair: 5. Changes are against Bend 2.0.40; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| adamw | 2.0.39 | 17869.9 | 0.00% | 3681.0 | 1.21% | 0.847 | **+6.21%** | **+4.41%** | b80a7888e4fc8673 |
| adamw | 2.0.40 | 16825.5 | 0.00% | 3525.4 | 0.60% | 0.813 |  |  | b80a7888e4fc8673 |
| attention-step | 2.0.39 | 19641.6 | 0.00% | 3823.4 | 0.65% | 0.851 | **+1.83%** | +2.39% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.40 | 19289.3 | 0.00% | 3734.2 | 0.93% | 0.834 |  |  | bb7f7e1c79c25bb7 |
| block-step | 2.0.39 | 31673.1 | 0.00% | 6139.8 | 0.20% | 1.368 | **+1.73%** | +0.63% | 400cae69095e09cf |
| block-step | 2.0.40 | 31135.0 | 0.00% | 6101.4 | 0.45% | 1.360 |  |  | 400cae69095e09cf |
| bpe-encode | 2.0.39 | 177706.5 | 0.00% | 33508.7 | 1.91% | 7.329 | **-8.48%** | **-22.42%** | 770398c19951fa8c |
| bpe-encode | 2.0.40 | 194163.1 | 0.00% | 43190.7 | 0.60% | 9.421 |  |  | 770398c19951fa8c |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2554.7 | 0.43% | 0.573 | **-0.89%** | -2.88% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.40 | 14031.7 | 0.00% | 2630.5 | 0.65% | 0.589 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3014.0 | 1.02% | 0.670 | **+2.42%** | **+3.32%** | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.40 | 13443.7 | 0.00% | 2917.0 | 0.96% | 0.648 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2439.2 | 14.16% | 0.545 | **+2.63%** | +2.05% | ff8b18c16b517923 |
| matvec-bands | 2.0.40 | 10361.8 | 0.00% | 2390.3 | 1.51% | 0.535 |  |  | ff8b18c16b517923 |
| mnist-fork | 2.0.39 | 13395.4 | 0.00% | 2435.8 | 1.01% | 0.543 | **+6.27%** | **+5.87%** | 2d83be930d21fb9f |
| mnist-fork | 2.0.40 | 12605.0 | 0.00% | 2300.7 | 0.67% | 0.512 |  |  | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3376.2 | 0.86% | 0.748 | **+2.10%** | **+3.27%** | 2d83be930d21fb9f |
| mnist-step | 2.0.40 | 15611.7 | 0.00% | 3269.3 | 0.69% | 0.725 |  |  | 2d83be930d21fb9f |
| read-bf16 | 2.0.39 | 161.6 | 0.00% | 59.1 | 1.14% | 0.027 | **+68.16%** | **+20.70%** | d09cf49a5e86a7f6 |
| read-bf16 | 2.0.40 | 96.1 | 0.00% | 49.0 | 2.03% | 0.032 |  |  | d09cf49a5e86a7f6 |
| read-binary | 2.0.39 | 21.2 | 0.00% | 20.7 | 1.35% | 0.016 | +0.00% | -0.10% | 9b44f947a6f6c6b9 |
| read-binary | 2.0.40 | 21.2 | 0.00% | 20.7 | 1.45% | 0.017 |  |  | 9b44f947a6f6c6b9 |
| read-native | 2.0.39 | 600.2 | 0.00% | 337.8 | 4.00% | 0.087 | **+2.14%** | +1.37% | 9b44f947a6f6c6b9 |
| read-native | 2.0.40 | 587.6 | 0.00% | 333.2 | 5.75% | 0.088 |  |  | 9b44f947a6f6c6b9 |
| rmsnorm-step | 2.0.39 | 11815.6 | 0.00% | 2332.9 | 0.52% | 0.519 | **+41.68%** | **+43.31%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.40 | 8339.9 | 0.00% | 1627.9 | 0.52% | 0.365 |  |  | 37901ab4cff27378 |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2281.5 | 1.71% | 0.504 | **+3.01%** | +1.93% | debeda8b7bc50c1f |
| softmax-ce | 2.0.40 | 7590.7 | 0.00% | 2238.4 | 0.75% | 0.495 |  |  | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.39 | 2703.9 | 0.00% | 595.7 | 2.24% | 0.143 | **+9.23%** | **+8.41%** | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.40 | 2475.4 | 0.00% | 549.5 | 2.24% | 0.133 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.40 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| adamw | 9244.0 | 3107.9 | 0.715 | 1.82x | 1.13x | 1.14x | yes |
| attention-step | 9017.5 | 2731.8 | 0.608 | 2.14x | 1.37x | 1.37x | yes |
| block-step | 15014.4 | 5003.5 | 1.123 | 2.07x | 1.22x | 1.21x | yes |
| bpe-encode | 275.4 | 70.7 | 0.024 | 705.05x | 611.26x | 389.31x | yes |
| gemm-fork | 8117.3 | 2244.9 | 0.501 | 1.73x | 1.17x | 1.17x | yes |
| gemm-tile8 | 8121.9 | 2250.4 | 0.504 | 1.66x | 1.30x | 1.29x | yes |
| matvec-bands | 3258.5 | 1028.2 | 0.245 | 3.18x | 2.32x | 2.19x | yes |
| mnist-fork | 6326.0 | 1774.8 | 0.409 | 1.99x | 1.30x | 1.25x | yes |
| mnist-step | 6326.0 | 1777.0 | 0.409 | 2.47x | 1.84x | 1.77x | yes |
| read-bf16 | 27.8 | 32.8 | 0.020 | 3.46x | 1.50x | 1.58x | yes |
| read-binary | 11.8 | 17.2 | 0.015 | 1.80x | 1.21x | 1.16x | yes |
| read-native | 11.8 | 17.2 | 0.015 | 49.96x | 19.38x | 5.89x | yes |
| rmsnorm-step | 1752.4 | 650.0 | 0.147 | 4.76x | 2.50x | 2.48x | yes |
| softmax-ce | 1603.0 | 501.2 | 0.120 | 4.74x | 4.47x | 4.11x | yes |
| softmax-ce-array | 1603.0 | 505.2 | 0.122 | 1.54x | 1.09x | 1.09x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| adamw | 2.0.39 | 0.847 | 0.850 | 1.00x | yes |
| adamw | 2.0.40 | 0.813 | 0.810 | 1.00x | yes |
| attention-step | 2.0.39 | 0.851 | 0.242 | 3.52x | yes |
| attention-step | 2.0.40 | 0.834 | 0.205 | 4.06x | yes |
| block-step | 2.0.39 | 1.368 | 0.335 | 4.08x | yes |
| block-step | 2.0.40 | 1.360 | 0.292 | 4.66x | yes |
| bpe-encode | 2.0.39 | 7.329 | 7.327 | 1.00x | yes |
| bpe-encode | 2.0.40 | 9.421 | 9.414 | 1.00x | yes |
| gemm-fork | 2.0.39 | 0.573 | 0.280 | 2.05x | yes |
| gemm-fork | 2.0.40 | 0.589 | 0.263 | 2.24x | yes |
| gemm-tile8 | 2.0.39 | 0.670 | 0.679 | 0.99x | yes |
| gemm-tile8 | 2.0.40 | 0.648 | 0.663 | 0.98x | yes |
| matvec-bands | 2.0.39 | 0.545 | 0.126 | 4.33x | yes |
| matvec-bands | 2.0.40 | 0.535 | 0.110 | 4.86x | yes |
| mnist-fork | 2.0.39 | 0.543 | 0.490 | 1.11x | yes |
| mnist-fork | 2.0.40 | 0.512 | 0.439 | 1.17x | yes |
| mnist-step | 2.0.39 | 0.748 | 0.732 | 1.02x | yes |
| mnist-step | 2.0.40 | 0.725 | 0.659 | 1.10x | yes |
| read-bf16 | 2.0.39 | 0.027 | 0.035 | 0.78x | yes |
| read-bf16 | 2.0.40 | 0.032 | 0.033 | 0.95x | yes |
| read-binary | 2.0.39 | 0.016 | 0.021 | 0.76x | yes |
| read-binary | 2.0.40 | 0.017 | 0.023 | 0.74x | yes |
| read-native | 2.0.39 | 0.087 | 0.159 | 0.55x | yes |
| read-native | 2.0.40 | 0.088 | 0.127 | 0.69x | yes |
| rmsnorm-step | 2.0.39 | 0.519 | 0.516 | 1.00x | yes |
| rmsnorm-step | 2.0.40 | 0.365 | 0.369 | 0.99x | yes |
| softmax-ce | 2.0.39 | 0.504 | 0.509 | 0.99x | yes |
| softmax-ce | 2.0.40 | 0.495 | 0.490 | 1.01x | yes |
| softmax-ce-array | 2.0.39 | 0.143 | 0.145 | 0.99x | yes |
| softmax-ce-array | 2.0.40 | 0.133 | 0.139 | 0.95x | yes |

## GPU targets (medians: the whole run's wall time, and its kernels' time on the device from nsys)

| workload | bend | s | spread | kernel ms | spread | kernels | hash | same output as the CPU |
|---|---|---:|---:|---:|---:|---:|---|---|
| block-step | 2.0.39 | 1.242 | 162.17% | 205.9 | 2.92% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| block-step | 2.0.40 | 3.189 | 65.87% | 179.3 | 2.98% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| gemm-tile8 | 2.0.39 | 2.387 | 88.62% | 55.2 | 8.99% | 120 | 0c6d7fee9a7ddf37 | yes |
| gemm-tile8 | 2.0.40 | 2.366 | 88.91% | 55.6 | 13.69% | 120 | 0c6d7fee9a7ddf37 | yes |
| rmsnorm-step | 2.0.39 | 6.003 | 35.86% | 3277.7 | 3.51% | 5000 | 37901ab4cff27378 | yes |
| rmsnorm-step | 2.0.40 | 5.722 | 35.61% | 3118.6 | 1.39% | 5000 | 37901ab4cff27378 | yes |

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
| loadavg_start | 0.50 0.20 0.07 |
| loadavg_end | 1.69 1.62 0.99 |
| pre_other_processes | claude x2, agents idle 1.3% |
| pre_cpu3_sibling | cpu4 0% |
| pre_perf_event_paranoid | 1 |
| busy | no |

## Beyond noise or differing outputs

- adamw: 2.0.39 instructions +6.21% against 2.0.40 (noise 0.10%)
- adamw: 2.0.39 cycles +4.41% against 2.0.40 (noise 1.21%)
- attention-step: 2.0.39 instructions +1.83% against 2.0.40 (noise 0.10%)
- block-step: 2.0.39 instructions +1.73% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 instructions -8.48% against 2.0.40 (noise 0.10%)
- bpe-encode: 2.0.39 cycles -22.42% against 2.0.40 (noise 1.91%)
- gemm-fork: 2.0.39 instructions -0.89% against 2.0.40 (noise 0.10%)
- gemm-tile8: 2.0.39 instructions +2.42% against 2.0.40 (noise 0.10%)
- gemm-tile8: 2.0.39 cycles +3.32% against 2.0.40 (noise 1.02%)
- matvec-bands: 2.0.39 instructions +2.63% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 instructions +6.27% against 2.0.40 (noise 0.10%)
- mnist-fork: 2.0.39 cycles +5.87% against 2.0.40 (noise 1.01%)
- mnist-step: 2.0.39 instructions +2.10% against 2.0.40 (noise 0.10%)
- mnist-step: 2.0.39 cycles +3.27% against 2.0.40 (noise 1.00%)
- read-bf16: 2.0.39 instructions +68.16% against 2.0.40 (noise 0.10%)
- read-bf16: 2.0.39 cycles +20.70% against 2.0.40 (noise 2.03%)
- read-native: 2.0.39 instructions +2.14% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 instructions +41.68% against 2.0.40 (noise 0.10%)
- rmsnorm-step: 2.0.39 cycles +43.31% against 2.0.40 (noise 1.00%)
- softmax-ce: 2.0.39 instructions +3.01% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 instructions +9.23% against 2.0.40 (noise 0.10%)
- softmax-ce-array: 2.0.39 cycles +8.41% against 2.0.40 (noise 2.24%)
