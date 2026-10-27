# 2026-10-25-e

Rounds per pair: 5. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| block-step | 2.0.35 | 31397.3 | 0.00% | 6060.6 | 1.72% | 1.357 | -0.01% | -0.62% | 4afdd96850039587 |
| block-step | 2.0.36 | 31397.3 | 0.00% | 6109.1 | 2.08% | 1.373 | -0.01% | +0.18% | 4afdd96850039587 |
| block-step | 2.0.37 | 31397.3 | 0.00% | 6143.5 | 3.75% | 1.374 | -0.01% | +0.74% | 4afdd96850039587 |
| block-step | 2.0.38 | 31400.6 | 0.00% | 6091.8 | 2.34% | 1.367 | +0.00% | -0.11% | 4afdd96850039587 |
| block-step | 2.0.39 | 31400.6 | 0.00% | 6098.4 | 1.18% | 1.365 |  |  | 4afdd96850039587 |
| gemm-fork | 2.0.35 | 13906.9 | 0.00% | 2624.0 | 0.97% | 0.593 | -0.00% | +2.46% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.36 | 13906.9 | 0.00% | 2636.3 | 1.19% | 0.599 | -0.00% | +2.94% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.37 | 13906.9 | 0.00% | 2579.7 | 4.67% | 0.585 | -0.00% | +0.73% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2620.6 | 0.80% | 0.594 | +0.00% | +2.32% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2561.0 | 0.83% | 0.580 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.35 | 13769.2 | 0.00% | 3026.2 | 1.73% | 0.677 | -0.00% | -0.21% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.36 | 13769.2 | 0.00% | 3033.7 | 1.02% | 0.681 | -0.00% | +0.04% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.37 | 13769.2 | 0.00% | 2960.2 | 0.69% | 0.663 | -0.00% | -2.39% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2967.2 | 0.51% | 0.664 | -0.00% | -2.15% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3032.5 | 3.70% | 0.680 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.35 | 10634.6 | 0.00% | 2247.7 | 12.20% | 0.513 | -0.00% | -2.62% | ff8b18c16b517923 |
| matvec-bands | 2.0.36 | 10634.6 | 0.00% | 2389.3 | 10.14% | 0.538 | -0.00% | +3.51% | ff8b18c16b517923 |
| matvec-bands | 2.0.37 | 10634.6 | 0.00% | 2348.4 | 5.30% | 0.532 | -0.00% | +1.74% | ff8b18c16b517923 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2290.2 | 11.49% | 0.520 | -0.00% | -0.78% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2308.2 | 12.70% | 0.524 |  |  | ff8b18c16b517923 |
| mnist-step | 2.0.35 | 22263.6 | 0.00% | 4805.5 | 0.74% | 1.063 | **+39.68%** | **+38.62%** | 2d83be930d21fb9f |
| mnist-step | 2.0.36 | 22124.2 | 0.00% | 4630.8 | 1.56% | 1.029 | **+38.80%** | **+33.58%** | 2d83be930d21fb9f |
| mnist-step | 2.0.37 | 22155.3 | 0.00% | 4627.6 | 0.79% | 1.027 | **+39.00%** | **+33.49%** | 2d83be930d21fb9f |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4562.9 | 1.39% | 1.017 | **+37.26%** | **+31.62%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3466.6 | 1.62% | 0.770 |  |  | 2d83be930d21fb9f |
| softmax-ce | 2.0.35 | 22363.7 | 0.00% | 7025.5 | 1.28% | 1.550 | **+186.01%** | **+187.85%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.36 | 21790.3 | 0.00% | 6779.0 | 2.07% | 1.496 | **+178.68%** | **+177.75%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.37 | 21883.2 | 0.00% | 6810.1 | 0.56% | 1.495 | **+179.86%** | **+179.03%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.38 | 22152.3 | 0.00% | 6754.0 | 2.07% | 1.489 | **+183.31%** | **+176.73%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2440.7 | 3.31% | 0.545 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.39 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| gemm-tile8 | 8121.9 | 2278.4 | 0.515 | 1.70x | 1.33x | 1.32x | yes |
| matvec-bands | 3258.5 | 1031.2 | 0.246 | 3.26x | 2.24x | 2.13x | yes |
| softmax-ce | 1603.0 | 511.2 | 0.125 | 4.88x | 4.77x | 4.36x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| block-step | 2.0.35 | 1.357 | 0.307 | 4.42x | yes |
| block-step | 2.0.36 | 1.373 | 0.308 | 4.45x | yes |
| block-step | 2.0.37 | 1.374 | 0.308 | 4.46x | yes |
| block-step | 2.0.38 | 1.367 | 0.308 | 4.44x | yes |
| block-step | 2.0.39 | 1.365 | 0.309 | 4.42x | yes |
| gemm-fork | 2.0.35 | 0.593 | 0.262 | 2.27x | yes |
| gemm-fork | 2.0.36 | 0.599 | 0.277 | 2.16x | yes |
| gemm-fork | 2.0.37 | 0.585 | 0.268 | 2.19x | yes |
| gemm-fork | 2.0.38 | 0.594 | 0.281 | 2.11x | yes |
| gemm-fork | 2.0.39 | 0.580 | 0.265 | 2.19x | yes |
| gemm-tile8 | 2.0.35 | 0.677 | 0.678 | 1.00x | yes |
| gemm-tile8 | 2.0.36 | 0.681 | 0.683 | 1.00x | yes |
| gemm-tile8 | 2.0.37 | 0.663 | 0.678 | 0.98x | yes |
| gemm-tile8 | 2.0.38 | 0.664 | 0.671 | 0.99x | yes |
| gemm-tile8 | 2.0.39 | 0.680 | 0.682 | 1.00x | yes |
| matvec-bands | 2.0.35 | 0.513 | 0.128 | 4.00x | yes |
| matvec-bands | 2.0.36 | 0.538 | 0.127 | 4.24x | yes |
| matvec-bands | 2.0.37 | 0.532 | 0.125 | 4.24x | yes |
| matvec-bands | 2.0.38 | 0.520 | 0.129 | 4.04x | yes |
| matvec-bands | 2.0.39 | 0.524 | 0.127 | 4.12x | yes |
| mnist-step | 2.0.35 | 1.063 | 1.002 | 1.06x | yes |
| mnist-step | 2.0.36 | 1.029 | 0.996 | 1.03x | yes |
| mnist-step | 2.0.37 | 1.027 | 0.979 | 1.05x | yes |
| mnist-step | 2.0.38 | 1.017 | 0.985 | 1.03x | yes |
| mnist-step | 2.0.39 | 0.770 | 0.747 | 1.03x | yes |
| softmax-ce | 2.0.35 | 1.550 | 1.546 | 1.00x | yes |
| softmax-ce | 2.0.36 | 1.496 | 1.493 | 1.00x | yes |
| softmax-ce | 2.0.37 | 1.495 | 1.494 | 1.00x | yes |
| softmax-ce | 2.0.38 | 1.489 | 1.494 | 1.00x | yes |
| softmax-ce | 2.0.39 | 0.545 | 0.540 | 1.01x | yes |

## Beyond noise or differing outputs

- mnist-step: 2.0.35 instructions +39.68% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.35 cycles +38.62% against 2.0.39 (noise 1.62%)
- mnist-step: 2.0.36 instructions +38.80% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.36 cycles +33.58% against 2.0.39 (noise 1.62%)
- mnist-step: 2.0.37 instructions +39.00% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.37 cycles +33.49% against 2.0.39 (noise 1.62%)
- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +31.62% against 2.0.39 (noise 1.62%)
- softmax-ce: 2.0.35 instructions +186.01% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.35 cycles +187.85% against 2.0.39 (noise 3.31%)
- softmax-ce: 2.0.36 instructions +178.68% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.36 cycles +177.75% against 2.0.39 (noise 3.31%)
- softmax-ce: 2.0.37 instructions +179.86% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.37 cycles +179.03% against 2.0.39 (noise 3.31%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +176.73% against 2.0.39 (noise 3.31%)
