# 2026-10-25-c

Rounds per pair: 5. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| block-step | 2.0.35 | 31397.3 | 0.00% | 6130.4 | 2.05% | 1.713 | -0.01% | -0.48% | 4afdd96850039587 |
| block-step | 2.0.36 | 31397.3 | 0.00% | 6172.2 | 0.47% | 1.739 | -0.01% | +0.20% | 4afdd96850039587 |
| block-step | 2.0.37 | 31397.3 | 0.00% | 6221.2 | 1.50% | 1.713 | -0.01% | +0.99% | 4afdd96850039587 |
| block-step | 2.0.38 | 31400.6 | 0.00% | 6161.3 | 1.64% | 1.726 | -0.00% | +0.02% | 4afdd96850039587 |
| block-step | 2.0.39 | 31400.6 | 0.00% | 6160.1 | 1.38% | 1.754 |  |  | 4afdd96850039587 |
| gemm-fork | 2.0.35 | 13906.9 | 0.00% | 2637.9 | 1.27% | 0.713 | -0.00% | +1.65% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.36 | 13906.9 | 0.00% | 2654.5 | 1.26% | 0.757 | -0.00% | +2.29% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.37 | 13906.9 | 0.00% | 2590.9 | 0.84% | 0.732 | -0.00% | -0.16% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2648.8 | 0.97% | 0.757 | +0.00% | +2.07% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2595.1 | 0.66% | 0.727 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.35 | 13769.2 | 0.00% | 3015.4 | 1.55% | 0.835 | -0.00% | +0.14% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.36 | 13769.2 | 0.00% | 3030.6 | 1.36% | 0.846 | -0.00% | +0.65% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.37 | 13769.2 | 0.00% | 2943.3 | 2.30% | 0.815 | -0.00% | -2.25% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2947.5 | 6.79% | 0.831 | +0.00% | -2.11% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3011.1 | 0.78% | 0.840 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.35 | 10634.6 | 0.00% | 2203.9 | 7.04% | 0.573 | -0.00% | +1.93% | ff8b18c16b517923 |
| matvec-bands | 2.0.36 | 10634.6 | 0.00% | 2183.2 | 9.17% | 0.532 | -0.00% | +0.97% | ff8b18c16b517923 |
| matvec-bands | 2.0.37 | 10634.6 | 0.00% | 2180.8 | 4.64% | 0.575 | -0.00% | +0.86% | ff8b18c16b517923 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2183.7 | 2.81% | 0.530 | -0.00% | +0.99% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2162.2 | 3.90% | 0.574 |  |  | ff8b18c16b517923 |
| mnist-step | 2.0.35 | 22263.6 | 0.00% | 4852.3 | 0.99% | 1.337 | **+39.68%** | **+37.79%** | 2d83be930d21fb9f |
| mnist-step | 2.0.36 | 22124.2 | 0.00% | 4681.9 | 0.78% | 1.298 | **+38.80%** | **+32.95%** | 2d83be930d21fb9f |
| mnist-step | 2.0.37 | 22155.3 | 0.00% | 4704.7 | 2.24% | 1.284 | **+39.00%** | **+33.60%** | 2d83be930d21fb9f |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4606.0 | 0.91% | 1.278 | **+37.26%** | **+30.80%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.2 | 0.00% | 3521.5 | 1.26% | 0.971 |  |  | 2d83be930d21fb9f |
| softmax-ce | 2.0.35 | 22363.7 | 0.00% | 7118.8 | 0.71% | 1.871 | **+186.01%** | **+181.76%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.36 | 21790.3 | 0.00% | 6923.6 | 1.53% | 1.811 | **+178.68%** | **+174.04%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.37 | 21883.2 | 0.00% | 6910.0 | 1.18% | 1.837 | **+179.86%** | **+173.50%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.38 | 22152.4 | 0.00% | 6853.8 | 0.50% | 1.805 | **+183.31%** | **+171.28%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2526.5 | 4.01% | 0.667 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.39 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| gemm-tile8 | 8121.9 | 2287.0 | 0.637 | 1.70x | 1.32x | 1.32x | yes |
| matvec-bands | 3258.5 | 1106.3 | 0.296 | 3.26x | 1.95x | 1.94x | yes |
| softmax-ce | 1603.0 | 522.9 | 0.154 | 4.88x | 4.83x | 4.33x | yes |

## Beyond noise or differing outputs

- mnist-step: 2.0.35 instructions +39.68% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.35 cycles +37.79% against 2.0.39 (noise 1.26%)
- mnist-step: 2.0.36 instructions +38.80% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.36 cycles +32.95% against 2.0.39 (noise 1.26%)
- mnist-step: 2.0.37 instructions +39.00% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.37 cycles +33.60% against 2.0.39 (noise 2.24%)
- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +30.80% against 2.0.39 (noise 1.26%)
- softmax-ce: 2.0.35 instructions +186.01% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.35 cycles +181.76% against 2.0.39 (noise 4.01%)
- softmax-ce: 2.0.36 instructions +178.68% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.36 cycles +174.04% against 2.0.39 (noise 4.01%)
- softmax-ce: 2.0.37 instructions +179.86% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.37 cycles +173.50% against 2.0.39 (noise 4.01%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +171.28% against 2.0.39 (noise 4.01%)
