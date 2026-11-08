# 2026-11-08-2.0.32-2.0.34

Rounds per pair: 5. Changes are against Bend 2.0.35; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| adamw | 2.0.32 | 17869.9 | 0.00% | 3667.5 | 1.61% | 0.848 | +0.00% | +0.19% | b80a7888e4fc8673 |
| adamw | 2.0.33 | 17869.9 | 0.00% | 3668.4 | 1.34% | 0.852 | +0.00% | +0.21% | b80a7888e4fc8673 |
| adamw | 2.0.34 | 17869.9 | 0.00% | 3673.2 | 0.77% | 0.852 | +0.00% | +0.34% | b80a7888e4fc8673 |
| adamw | 2.0.35 | 17869.9 | 0.00% | 3660.6 | 1.59% | 0.850 |  |  | b80a7888e4fc8673 |
| attention-step | 2.0.32 | 59732.4 | 0.00% | 10017.1 | 0.37% | 2.203 | **+204.16%** | **+162.54%** | bb7f7e1c79c25bb7 |
| attention-step | 2.0.33 | 19993.9 | 0.00% | 3913.3 | 0.19% | 0.872 | **+1.81%** | +2.56% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.34 | 19993.9 | 0.00% | 3913.1 | 0.35% | 0.871 | **+1.81%** | +2.56% | bb7f7e1c79c25bb7 |
| attention-step | 2.0.35 | 19638.5 | 0.00% | 3815.5 | 0.70% | 0.849 |  |  | bb7f7e1c79c25bb7 |
| block-step | 2.0.32 | 109403.7 | 0.00% | 18037.1 | 0.28% | 3.966 | **+245.45%** | **+194.59%** | 400cae69095e09cf |
| block-step | 2.0.33 | 31845.9 | 0.00% | 6181.5 | 0.34% | 1.381 | **+0.56%** | +0.96% | 400cae69095e09cf |
| block-step | 2.0.34 | 31845.9 | 0.00% | 6182.4 | 0.29% | 1.376 | **+0.56%** | +0.97% | 400cae69095e09cf |
| block-step | 2.0.35 | 31669.8 | 0.00% | 6122.7 | 0.67% | 1.366 |  |  | 400cae69095e09cf |
| bpe-encode | 2.0.32 | 194174.8 | 0.00% | 35627.4 | 0.90% | 7.782 | +0.00% | -1.05% | 770398c19951fa8c |
| bpe-encode | 2.0.33 | 194174.8 | 0.00% | 37363.6 | 0.80% | 8.172 | +0.00% | +3.77% | 770398c19951fa8c |
| bpe-encode | 2.0.34 | 194174.8 | 0.00% | 37398.5 | 6.28% | 8.183 | +0.00% | +3.87% | 770398c19951fa8c |
| bpe-encode | 2.0.35 | 194170.7 | 0.00% | 36005.3 | 1.47% | 7.864 |  |  | 770398c19951fa8c |
| gemm-fork | 2.0.32 | 52095.4 | 0.00% | 8528.7 | 0.53% | 1.872 | **+274.60%** | **+227.36%** | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.33 | 13906.9 | 0.00% | 2611.7 | 0.40% | 0.586 | -0.00% | +0.25% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.34 | 13906.9 | 0.00% | 2611.8 | 1.13% | 0.586 | +0.00% | +0.25% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.35 | 13906.9 | 0.00% | 2605.3 | 1.07% | 0.583 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.32 | 13769.2 | 0.00% | 2935.6 | 1.08% | 0.652 | +0.00% | -1.54% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.33 | 13769.2 | 0.00% | 2983.3 | 1.45% | 0.664 | +0.00% | +0.06% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.34 | 13769.2 | 0.00% | 2996.8 | 1.22% | 0.667 | +0.00% | +0.51% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.35 | 13769.2 | 0.00% | 2981.7 | 1.89% | 0.663 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.32 | 10634.6 | 0.00% | 2503.1 | 14.32% | 0.558 | -0.00% | -0.85% | ff8b18c16b517923 |
| matvec-bands | 2.0.33 | 10634.6 | 0.00% | 2553.2 | 14.01% | 0.566 | -0.00% | +1.13% | ff8b18c16b517923 |
| matvec-bands | 2.0.34 | 10634.6 | 0.00% | 2515.8 | 9.75% | 0.560 | -0.00% | -0.35% | ff8b18c16b517923 |
| matvec-bands | 2.0.35 | 10634.6 | 0.00% | 2524.7 | 11.20% | 0.561 |  |  | ff8b18c16b517923 |
| mnist-fork | 2.0.32 | 46504.7 | 0.00% | 8064.2 | 0.81% | 1.771 | **+237.81%** | **+209.55%** | 2d83be930d21fb9f |
| mnist-fork | 2.0.33 | 13766.5 | 0.00% | 2610.1 | 0.84% | 0.580 | +0.00% | +0.19% | 2d83be930d21fb9f |
| mnist-fork | 2.0.34 | 13766.5 | 0.00% | 2611.0 | 0.16% | 0.581 | +0.00% | +0.22% | 2d83be930d21fb9f |
| mnist-fork | 2.0.35 | 13766.4 | 0.00% | 2605.2 | 1.08% | 0.580 |  |  | 2d83be930d21fb9f |
| mnist-step | 2.0.32 | 22263.8 | 0.00% | 4658.9 | 0.56% | 1.029 | +0.00% | -0.98% | 2d83be930d21fb9f |
| mnist-step | 2.0.33 | 22263.8 | 0.00% | 4690.2 | 0.66% | 1.036 | +0.00% | -0.31% | 2d83be930d21fb9f |
| mnist-step | 2.0.34 | 22263.8 | 0.00% | 4682.3 | 1.64% | 1.033 | +0.00% | -0.48% | 2d83be930d21fb9f |
| mnist-step | 2.0.35 | 22263.6 | 0.00% | 4704.9 | 1.20% | 1.040 |  |  | 2d83be930d21fb9f |
| read-native | 2.0.32 | 600.2 | 0.00% | 342.0 | 4.35% | 0.087 | -0.00% | +2.61% | 9b44f947a6f6c6b9 |
| read-native | 2.0.33 | 600.2 | 0.00% | 333.3 | 5.55% | 0.087 | -0.00% | -0.00% | 9b44f947a6f6c6b9 |
| read-native | 2.0.34 | 600.2 | 0.00% | 335.6 | 3.48% | 0.086 | -0.00% | +0.68% | 9b44f947a6f6c6b9 |
| read-native | 2.0.35 | 600.2 | 0.00% | 333.3 | 6.95% | 0.086 |  |  | 9b44f947a6f6c6b9 |
| rmsnorm-step | 2.0.32 | 11756.8 | 0.00% | 2648.1 | 0.37% | 0.584 | **-0.50%** | **+13.35%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.33 | 11756.8 | 0.00% | 2666.1 | 0.43% | 0.588 | **-0.50%** | **+14.13%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.34 | 11756.8 | 0.00% | 2668.5 | 0.28% | 0.588 | **-0.50%** | **+14.23%** | 37901ab4cff27378 |
| rmsnorm-step | 2.0.35 | 11815.6 | 0.00% | 2336.1 | 0.45% | 0.518 |  |  | 37901ab4cff27378 |
| softmax-ce | 2.0.32 | 22363.7 | 0.00% | 6741.8 | 0.35% | 1.472 | +0.00% | +0.00% | debeda8b7bc50c1f |
| softmax-ce | 2.0.33 | 22363.7 | 0.00% | 6734.0 | 0.52% | 1.468 | +0.00% | -0.11% | debeda8b7bc50c1f |
| softmax-ce | 2.0.34 | 22363.7 | 0.00% | 6724.1 | 0.89% | 1.469 | +0.00% | -0.26% | debeda8b7bc50c1f |
| softmax-ce | 2.0.35 | 22363.7 | 0.00% | 6741.5 | 0.59% | 1.477 |  |  | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.32 | 2703.9 | 0.00% | 590.3 | 1.88% | 0.142 | +0.00% | +0.33% | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.33 | 2703.9 | 0.00% | 596.8 | 2.65% | 0.145 | +0.00% | +1.43% | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.34 | 2703.9 | 0.00% | 589.8 | 1.48% | 0.142 | +0.00% | +0.24% | debeda8b7bc50c1f |
| softmax-ce-array | 2.0.35 | 2703.9 | 0.00% | 588.4 | 2.32% | 0.142 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.35 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| adamw | 9244.0 | 3073.6 | 0.715 | 1.93x | 1.19x | 1.19x | yes |
| attention-step | 9017.5 | 2726.7 | 0.611 | 2.18x | 1.40x | 1.39x | yes |
| block-step | 15014.4 | 4997.0 | 1.124 | 2.11x | 1.23x | 1.22x | yes |
| bpe-encode | 275.4 | 71.1 | 0.025 | 705.08x | 506.43x | 318.37x | yes |
| gemm-fork | 8117.3 | 2243.6 | 0.503 | 1.71x | 1.16x | 1.16x | yes |
| gemm-tile8 | 8121.9 | 2252.9 | 0.506 | 1.70x | 1.32x | 1.31x | yes |
| matvec-bands | 3258.5 | 1032.4 | 0.242 | 3.26x | 2.45x | 2.31x | yes |
| mnist-fork | 6326.0 | 1771.1 | 0.408 | 2.18x | 1.47x | 1.42x | yes |
| mnist-step | 6326.0 | 1776.1 | 0.410 | 3.52x | 2.65x | 2.54x | yes |
| read-native | 11.8 | 17.2 | 0.015 | 51.04x | 19.35x | 5.60x | yes |
| rmsnorm-step | 1752.4 | 647.0 | 0.147 | 6.74x | 3.61x | 3.52x | yes |
| softmax-ce | 1603.0 | 503.9 | 0.122 | 13.95x | 13.38x | 12.09x | yes |
| softmax-ce-array | 1603.0 | 505.5 | 0.123 | 1.69x | 1.16x | 1.16x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| adamw | 2.0.32 | 0.848 | 0.853 | 0.99x | yes |
| adamw | 2.0.33 | 0.852 | 0.846 | 1.01x | yes |
| adamw | 2.0.34 | 0.852 | 0.849 | 1.00x | yes |
| adamw | 2.0.35 | 0.850 | 0.848 | 1.00x | yes |
| attention-step | 2.0.32 | 2.203 | 0.560 | 3.94x | yes |
| attention-step | 2.0.33 | 0.872 | 0.327 | 2.67x | yes |
| attention-step | 2.0.34 | 0.871 | 0.329 | 2.65x | yes |
| attention-step | 2.0.35 | 0.849 | 0.237 | 3.59x | yes |
| block-step | 2.0.32 | 3.966 | 0.857 | 4.63x | yes |
| block-step | 2.0.33 | 1.381 | 0.444 | 3.11x | yes |
| block-step | 2.0.34 | 1.376 | 0.453 | 3.04x | yes |
| block-step | 2.0.35 | 1.366 | 0.337 | 4.06x | yes |
| bpe-encode | 2.0.32 | 7.782 | 7.762 | 1.00x | yes |
| bpe-encode | 2.0.33 | 8.172 | 8.188 | 1.00x | yes |
| bpe-encode | 2.0.34 | 8.183 | 8.161 | 1.00x | yes |
| bpe-encode | 2.0.35 | 7.864 | 7.865 | 1.00x | yes |
| gemm-fork | 2.0.32 | 1.872 | 0.710 | 2.64x | yes |
| gemm-fork | 2.0.33 | 0.586 | 0.317 | 1.85x | yes |
| gemm-fork | 2.0.34 | 0.586 | 0.311 | 1.88x | yes |
| gemm-fork | 2.0.35 | 0.583 | 0.269 | 2.17x | yes |
| gemm-tile8 | 2.0.32 | 0.652 | 0.656 | 0.99x | yes |
| gemm-tile8 | 2.0.33 | 0.664 | 0.667 | 1.00x | yes |
| gemm-tile8 | 2.0.34 | 0.667 | 0.680 | 0.98x | yes |
| gemm-tile8 | 2.0.35 | 0.663 | 0.673 | 0.99x | yes |
| matvec-bands | 2.0.32 | 0.558 | 0.128 | 4.37x | yes |
| matvec-bands | 2.0.33 | 0.566 | 0.125 | 4.53x | yes |
| matvec-bands | 2.0.34 | 0.560 | 0.126 | 4.47x | yes |
| matvec-bands | 2.0.35 | 0.561 | 0.126 | 4.47x | yes |
| mnist-fork | 2.0.32 | 1.771 | 1.139 | 1.55x | yes |
| mnist-fork | 2.0.33 | 0.580 | 0.590 | 0.98x | yes |
| mnist-fork | 2.0.34 | 0.581 | 0.582 | 1.00x | yes |
| mnist-fork | 2.0.35 | 0.580 | 0.546 | 1.06x | yes |
| mnist-step | 2.0.32 | 1.029 | 1.035 | 0.99x | yes |
| mnist-step | 2.0.33 | 1.036 | 1.027 | 1.01x | yes |
| mnist-step | 2.0.34 | 1.033 | 1.023 | 1.01x | yes |
| mnist-step | 2.0.35 | 1.040 | 0.956 | 1.09x | yes |
| read-native | 2.0.32 | 0.087 | 0.117 | 0.75x | yes |
| read-native | 2.0.33 | 0.087 | 0.140 | 0.62x | yes |
| read-native | 2.0.34 | 0.086 | 0.102 | 0.84x | yes |
| read-native | 2.0.35 | 0.086 | 0.126 | 0.68x | yes |
| rmsnorm-step | 2.0.32 | 0.584 | 0.582 | 1.00x | yes |
| rmsnorm-step | 2.0.33 | 0.588 | 0.586 | 1.00x | yes |
| rmsnorm-step | 2.0.34 | 0.588 | 0.585 | 1.01x | yes |
| rmsnorm-step | 2.0.35 | 0.518 | 0.519 | 1.00x | yes |
| softmax-ce | 2.0.32 | 1.472 | 1.460 | 1.01x | yes |
| softmax-ce | 2.0.33 | 1.468 | 1.474 | 1.00x | yes |
| softmax-ce | 2.0.34 | 1.469 | 1.454 | 1.01x | yes |
| softmax-ce | 2.0.35 | 1.477 | 1.470 | 1.00x | yes |
| softmax-ce-array | 2.0.32 | 0.142 | 0.144 | 0.98x | yes |
| softmax-ce-array | 2.0.33 | 0.145 | 0.144 | 1.00x | yes |
| softmax-ce-array | 2.0.34 | 0.142 | 0.144 | 0.99x | yes |
| softmax-ce-array | 2.0.35 | 0.142 | 0.149 | 0.96x | yes |

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
| loadavg_start | 0.09 0.71 1.46 |
| loadavg_end | 1.11 1.25 1.34 |
| pre_other_processes | claude x1, agents idle 7.1% |
| pre_cpu3_sibling | cpu4 0% |
| pre_perf_event_paranoid | 1 |
| busy | no |

## Beyond noise or differing outputs

- attention-step: 2.0.32 instructions +204.16% against 2.0.35 (noise 0.10%)
- attention-step: 2.0.32 cycles +162.54% against 2.0.35 (noise 1.00%)
- attention-step: 2.0.33 instructions +1.81% against 2.0.35 (noise 0.10%)
- attention-step: 2.0.34 instructions +1.81% against 2.0.35 (noise 0.10%)
- block-step: 2.0.32 instructions +245.45% against 2.0.35 (noise 0.10%)
- block-step: 2.0.32 cycles +194.59% against 2.0.35 (noise 1.00%)
- block-step: 2.0.33 instructions +0.56% against 2.0.35 (noise 0.10%)
- block-step: 2.0.34 instructions +0.56% against 2.0.35 (noise 0.10%)
- gemm-fork: 2.0.32 instructions +274.60% against 2.0.35 (noise 0.10%)
- gemm-fork: 2.0.32 cycles +227.36% against 2.0.35 (noise 1.07%)
- mnist-fork: 2.0.32 instructions +237.81% against 2.0.35 (noise 0.10%)
- mnist-fork: 2.0.32 cycles +209.55% against 2.0.35 (noise 1.08%)
- rmsnorm-step: 2.0.32 instructions -0.50% against 2.0.35 (noise 0.10%)
- rmsnorm-step: 2.0.32 cycles +13.35% against 2.0.35 (noise 1.00%)
- rmsnorm-step: 2.0.33 instructions -0.50% against 2.0.35 (noise 0.10%)
- rmsnorm-step: 2.0.33 cycles +14.13% against 2.0.35 (noise 1.00%)
- rmsnorm-step: 2.0.34 instructions -0.50% against 2.0.35 (noise 0.10%)
- rmsnorm-step: 2.0.34 cycles +14.23% against 2.0.35 (noise 1.00%)
