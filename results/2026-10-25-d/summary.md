# 2026-10-25-d

Rounds per pair: 7. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| block-step | 2.0.35 | 31397.3 | 0.00% | 6057.4 | 1.17% | 1.352 | -0.01% | -0.29% | 4afdd96850039587 |
| block-step | 2.0.36 | 31397.3 | 0.00% | 6103.4 | 0.94% | 1.364 | -0.01% | +0.47% | 4afdd96850039587 |
| block-step | 2.0.37 | 31397.3 | 0.00% | 6115.3 | 1.11% | 1.371 | -0.01% | +0.66% | 4afdd96850039587 |
| block-step | 2.0.38 | 31400.6 | 0.00% | 6069.2 | 0.48% | 1.356 | -0.00% | -0.10% | 4afdd96850039587 |
| block-step | 2.0.39 | 31400.6 | 0.00% | 6075.0 | 0.57% | 1.358 |  |  | 4afdd96850039587 |
| gemm-fork | 2.0.35 | 13906.9 | 0.00% | 2610.2 | 0.75% | 0.587 | -0.00% | +1.82% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.36 | 13906.9 | 0.00% | 2629.4 | 1.17% | 0.592 | -0.00% | +2.57% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.37 | 13906.9 | 0.00% | 2563.0 | 1.26% | 0.579 | -0.00% | -0.02% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2610.3 | 0.72% | 0.587 | -0.00% | +1.83% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2563.5 | 0.91% | 0.575 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.35 | 13769.2 | 0.00% | 3010.6 | 1.12% | 0.671 | -0.00% | -0.14% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.36 | 13769.2 | 0.00% | 3026.7 | 1.73% | 0.676 | -0.00% | +0.40% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.37 | 13769.2 | 0.00% | 2942.2 | 0.80% | 0.657 | -0.00% | -2.41% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2949.7 | 0.55% | 0.658 | +0.00% | -2.16% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3014.7 | 0.80% | 0.672 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.35 | 10634.6 | 0.00% | 2415.0 | 3.14% | 0.538 | -0.00% | +1.67% | ff8b18c16b517923 |
| matvec-bands | 2.0.36 | 10634.6 | 0.00% | 2387.4 | 7.05% | 0.537 | -0.00% | +0.51% | ff8b18c16b517923 |
| matvec-bands | 2.0.37 | 10634.6 | 0.00% | 2414.4 | 5.75% | 0.542 | -0.00% | +1.64% | ff8b18c16b517923 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2409.4 | 3.01% | 0.539 | +0.00% | +1.43% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2375.4 | 8.57% | 0.537 |  |  | ff8b18c16b517923 |
| mnist-step | 2.0.35 | 22263.6 | 0.00% | 4784.9 | 1.28% | 1.060 | **+39.68%** | **+38.43%** | 2d83be930d21fb9f |
| mnist-step | 2.0.36 | 22124.2 | 0.00% | 4629.8 | 1.25% | 1.024 | **+38.80%** | **+33.94%** | 2d83be930d21fb9f |
| mnist-step | 2.0.37 | 22155.3 | 0.00% | 4646.8 | 1.10% | 1.027 | **+39.00%** | **+34.43%** | 2d83be930d21fb9f |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4558.9 | 2.01% | 1.008 | **+37.26%** | **+31.89%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3456.5 | 1.15% | 0.767 |  |  | 2d83be930d21fb9f |
| softmax-ce | 2.0.35 | 22363.7 | 0.00% | 7014.8 | 1.23% | 1.538 | **+186.01%** | **+188.39%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.36 | 21790.3 | 0.00% | 6770.1 | 2.90% | 1.486 | **+178.68%** | **+178.33%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.37 | 21883.2 | 0.00% | 6801.2 | 0.47% | 1.494 | **+179.86%** | **+179.61%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.38 | 22152.3 | 0.00% | 6755.8 | 1.71% | 1.479 | **+183.31%** | **+177.75%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2432.4 | 3.53% | 0.541 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.39 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| gemm-tile8 | 8121.9 | 2266.0 | 0.512 | 1.70x | 1.33x | 1.31x | yes |
| matvec-bands | 3258.5 | 1025.2 | 0.243 | 3.26x | 2.32x | 2.20x | yes |
| softmax-ce | 1603.0 | 512.2 | 0.124 | 4.88x | 4.75x | 4.36x | yes |

## Beyond noise or differing outputs

- mnist-step: 2.0.35 instructions +39.68% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.35 cycles +38.43% against 2.0.39 (noise 1.28%)
- mnist-step: 2.0.36 instructions +38.80% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.36 cycles +33.94% against 2.0.39 (noise 1.25%)
- mnist-step: 2.0.37 instructions +39.00% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.37 cycles +34.43% against 2.0.39 (noise 1.15%)
- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +31.89% against 2.0.39 (noise 2.01%)
- softmax-ce: 2.0.35 instructions +186.01% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.35 cycles +188.39% against 2.0.39 (noise 3.53%)
- softmax-ce: 2.0.36 instructions +178.68% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.36 cycles +178.33% against 2.0.39 (noise 3.53%)
- softmax-ce: 2.0.37 instructions +179.86% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.37 cycles +179.61% against 2.0.39 (noise 3.53%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +177.75% against 2.0.39 (noise 3.53%)
