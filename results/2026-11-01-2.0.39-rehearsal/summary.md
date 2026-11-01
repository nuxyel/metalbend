# 2026-11-01-2.0.39-rehearsal

**A busy run** (other_processes): its timings are a diagnosis, not a result, and do not go in results/ or a README.

Rounds per pair: 5. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| adamw | 2.0.38 | 17869.9 | 0.00% | 3685.0 | 1.45% | 0.853 | -0.00% | +1.05% | b80a7888e4fc8673 |
| adamw | 2.0.39 | 17869.9 | 0.00% | 3646.7 | 3.19% | 0.848 |  |  | b80a7888e4fc8673 |
| attention-step | 2.0.38 | 19641.6 | 0.00% | 3834.5 | 0.39% | 0.861 | +0.00% | +0.20% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.39 | 19641.6 | 0.00% | 3826.8 | 0.48% | 0.865 |  |  | bb7f7e1c79c25bb7 |
| block-step | 2.0.38 | 31673.1 | 0.00% | 6138.0 | 0.32% | 1.381 | -0.00% | -0.43% | 400cae69095e09cf |
| block-step | 2.0.39 | 31673.1 | 0.00% | 6164.6 | 0.64% | 1.389 |  |  | 400cae69095e09cf |
| bpe-encode | 2.0.38 | 177706.5 | 0.00% | 33050.3 | 0.72% | 7.246 | -0.00% | -0.21% | 770398c19951fa8c |
| bpe-encode | 2.0.39 | 177706.5 | 0.00% | 33120.9 | 1.55% | 7.311 |  |  | 770398c19951fa8c |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2612.3 | 0.76% | 0.590 | +0.00% | +2.36% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2552.0 | 0.52% | 0.580 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2955.8 | 0.97% | 0.660 | +0.00% | -2.55% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3033.2 | 0.90% | 0.678 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2423.5 | 9.74% | 0.548 | -0.00% | -0.22% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2428.9 | 6.65% | 0.551 |  |  | ff8b18c16b517923 |
| mnist-fork | 2.0.38 | 13780.5 | 0.00% | 2587.5 | 0.20% | 0.580 | **+2.87%** | **+5.30%** | 2d83be930d21fb9f |
| mnist-fork | 2.0.39 | 13395.4 | 0.00% | 2457.2 | 0.72% | 0.551 |  |  | 2d83be930d21fb9f |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4444.7 | 0.75% | 0.985 | **+37.26%** | **+30.77%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3398.9 | 1.46% | 0.753 |  |  | 2d83be930d21fb9f |
| read-bf16 | 2.0.38 | 161.6 | 0.00% | 59.2 | 1.02% | 0.027 | +0.02% | +0.03% | d09cf49a5e86a7f6 |
| read-bf16 | 2.0.39 | 161.6 | 0.00% | 59.2 | 1.12% | 0.034 |  |  | d09cf49a5e86a7f6 |
| read-binary | 2.0.38 | 21.2 | 0.00% | 20.8 | 1.42% | 0.017 | -0.00% | +0.52% | 9b44f947a6f6c6b9 |
| read-binary | 2.0.39 | 21.2 | 0.00% | 20.7 | 1.50% | 0.017 |  |  | 9b44f947a6f6c6b9 |
| read-native | 2.0.38 | 600.2 | 0.00% | 332.8 | 7.90% | 0.088 | -0.00% | +1.68% | 9b44f947a6f6c6b9 |
| read-native | 2.0.39 | 600.2 | 0.00% | 327.3 | 8.62% | 0.086 |  |  | 9b44f947a6f6c6b9 |
| rmsnorm-step | 2.0.38 | 11815.7 | 0.00% | 2358.7 | 0.76% | 0.527 | +0.00% | +1.33% | 37901ab4cff27378 |
| rmsnorm-step | 2.0.39 | 11815.7 | 0.00% | 2327.6 | 0.53% | 0.519 |  |  | 37901ab4cff27378 |
| softmax-ce | 2.0.38 | 22152.4 | 0.00% | 6463.4 | 0.54% | 1.422 | **+183.31%** | **+184.43%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2272.4 | 1.30% | 0.510 |  |  | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.38 | 2703.9 | 0.00% | 590.5 | 1.66% | 0.143 | +0.00% | +0.07% | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.39 | 2703.9 | 0.00% | 590.1 | 1.63% | 0.143 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.39 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| adamw | 9244.0 | 3080.3 | 0.717 | 1.93x | 1.18x | 1.18x | yes |
| attention-step | 9017.6 | 2718.6 | 0.612 | 2.18x | 1.41x | 1.41x | yes |
| block-step | 15014.4 | 4997.9 | 1.128 | 2.11x | 1.23x | 1.23x | yes |
| bpe-encode | 275.4 | 71.6 | 0.025 | 645.27x | 462.72x | 287.83x | yes |
| gemm-fork | 8117.3 | 2257.3 | 0.507 | 1.71x | 1.13x | 1.14x | yes |
| gemm-tile8 | 8121.9 | 2261.9 | 0.509 | 1.70x | 1.34x | 1.33x | yes |
| matvec-bands | 3258.5 | 1025.8 | 0.247 | 3.26x | 2.37x | 2.23x | yes |
| mnist-fork | 6326.0 | 1770.9 | 0.409 | 2.12x | 1.39x | 1.35x | yes |
| mnist-step | 6326.0 | 1775.8 | 0.411 | 2.52x | 1.91x | 1.83x | yes |
| read-bf16 | 27.8 | 32.8 | 0.020 | 5.81x | 1.80x | 1.72x | yes |
| read-binary | 11.8 | 17.2 | 0.015 | 1.80x | 1.20x | 1.09x | yes |
| read-native | 11.8 | 17.2 | 0.015 | 50.99x | 19.01x | 5.64x | yes |
| rmsnorm-step | 1752.4 | 642.2 | 0.150 | 6.74x | 3.62x | 3.46x | yes |
| softmax-ce | 1603.0 | 503.9 | 0.123 | 4.88x | 4.51x | 4.15x | yes |
| softmax-ce-array | 1603.0 | 501.0 | 0.122 | 1.69x | 1.18x | 1.17x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| adamw | 2.0.38 | 0.853 | 0.856 | 1.00x | yes |
| adamw | 2.0.39 | 0.848 | 0.861 | 0.99x | yes |
| attention-step | 2.0.38 | 0.861 | 0.241 | 3.57x | yes |
| attention-step | 2.0.39 | 0.865 | 0.241 | 3.59x | yes |
| block-step | 2.0.38 | 1.381 | 0.337 | 4.10x | yes |
| block-step | 2.0.39 | 1.389 | 0.340 | 4.08x | yes |
| bpe-encode | 2.0.38 | 7.246 | 7.289 | 0.99x | yes |
| bpe-encode | 2.0.39 | 7.311 | 7.312 | 1.00x | yes |
| gemm-fork | 2.0.38 | 0.590 | 0.273 | 2.16x | yes |
| gemm-fork | 2.0.39 | 0.580 | 0.274 | 2.12x | yes |
| gemm-tile8 | 2.0.38 | 0.660 | 0.663 | 1.00x | yes |
| gemm-tile8 | 2.0.39 | 0.678 | 0.683 | 0.99x | yes |
| matvec-bands | 2.0.38 | 0.548 | 0.126 | 4.35x | yes |
| matvec-bands | 2.0.39 | 0.551 | 0.125 | 4.41x | yes |
| mnist-fork | 2.0.38 | 0.580 | 0.540 | 1.07x | yes |
| mnist-fork | 2.0.39 | 0.551 | 0.491 | 1.12x | yes |
| mnist-step | 2.0.38 | 0.985 | 0.975 | 1.01x | yes |
| mnist-step | 2.0.39 | 0.753 | 0.731 | 1.03x | yes |
| read-bf16 | 2.0.38 | 0.027 | 0.033 | 0.84x | yes |
| read-bf16 | 2.0.39 | 0.034 | 0.034 | 1.01x | yes |
| read-binary | 2.0.38 | 0.017 | 0.021 | 0.79x | yes |
| read-binary | 2.0.39 | 0.017 | 0.023 | 0.71x | yes |
| read-native | 2.0.38 | 0.088 | 0.128 | 0.69x | yes |
| read-native | 2.0.39 | 0.086 | 0.131 | 0.66x | yes |
| rmsnorm-step | 2.0.38 | 0.527 | 0.528 | 1.00x | yes |
| rmsnorm-step | 2.0.39 | 0.519 | 0.527 | 0.98x | yes |
| softmax-ce | 2.0.38 | 1.422 | 1.431 | 0.99x | yes |
| softmax-ce | 2.0.39 | 0.510 | 0.510 | 1.00x | yes |
| softmax-ce-array | 2.0.38 | 0.143 | 0.148 | 0.97x | yes |
| softmax-ce-array | 2.0.39 | 0.143 | 0.153 | 0.94x | yes |

## GPU targets (medians: the whole run's wall time, and its kernels' time on the device from nsys)

| workload | bend | s | spread | kernel ms | spread | kernels | hash | same output as the CPU |
|---|---|---:|---:|---:|---:|---:|---|---|
| block-step | 2.0.38 | 1.279 | 157.95% | 208.9 | 2.98% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| block-step | 2.0.39 | 3.256 | 65.26% | 204.6 | 6.00% | 345 | 015f98a384541840 | no, as oracles.tsv records (block-step:gpu) |
| gemm-tile8 | 2.0.38 | 2.382 | 88.12% | 53.4 | 8.95% | 120 | 0c6d7fee9a7ddf37 | yes |
| gemm-tile8 | 2.0.39 | 2.377 | 88.58% | 54.0 | 13.37% | 120 | 0c6d7fee9a7ddf37 | yes |
| rmsnorm-step | 2.0.38 | 5.912 | 37.33% | 3273.8 | 1.72% | 5000 | 37901ab4cff27378 | yes |
| rmsnorm-step | 2.0.39 | 6.028 | 34.65% | 3272.3 | 2.38% | 5000 | 37901ab4cff27378 | yes |

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
| loadavg_start | 1.96 1.27 1.37 |
| loadavg_end | 1.05 1.45 1.44 |
| pre_other_processes | codex-code-mode x1, codex x2, claude x1 |
| pre_cpu3_sibling | cpu4 0% |
| pre_perf_event_paranoid | 1 |
| busy | other_processes |

## Beyond noise or differing outputs

- mnist-fork: 2.0.38 instructions +2.87% against 2.0.39 (noise 0.10%)
- mnist-fork: 2.0.38 cycles +5.30% against 2.0.39 (noise 1.00%)
- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +30.77% against 2.0.39 (noise 1.46%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +184.43% against 2.0.39 (noise 1.30%)
