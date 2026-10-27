# 2026-10-25-b

Rounds per pair: 5. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| block-step | 2.0.35 | 31397.3 | 0.00% | 6123.0 | 1.43% | 1.434 | -0.01% | +0.01% | 4afdd96850039587 |
| block-step | 2.0.36 | 31397.3 | 0.00% | 6151.0 | 0.86% | 1.438 | -0.01% | +0.47% | 4afdd96850039587 |
| block-step | 2.0.37 | 31397.3 | 0.00% | 6180.9 | 1.02% | 1.447 | -0.01% | +0.96% | 4afdd96850039587 |
| block-step | 2.0.38 | 31400.6 | 0.00% | 6143.4 | 1.47% | 1.436 | -0.00% | +0.35% | 4afdd96850039587 |
| block-step | 2.0.39 | 31400.6 | 0.00% | 6122.2 | 1.56% | 1.451 |  |  | 4afdd96850039587 |
| gemm-fork | 2.0.35 | 13906.9 | 0.00% | 2645.8 | 1.54% | 0.620 | -0.00% | +2.19% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.36 | 13906.9 | 0.00% | 2656.6 | 11.03% | 0.639 | -0.00% | +2.61% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.37 | 13906.9 | 0.00% | 2596.7 | 0.79% | 0.633 | -0.00% | +0.30% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2631.8 | 1.68% | 0.627 | +0.00% | +1.65% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2589.0 | 1.50% | 0.611 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.35 | 13769.2 | 0.00% | 3021.1 | 0.71% | 0.696 | -0.00% | -0.35% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.36 | 13769.2 | 0.00% | 3048.5 | 2.67% | 0.715 | -0.00% | +0.56% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.37 | 13769.2 | 0.00% | 2953.4 | 0.27% | 0.684 | -0.00% | -2.58% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2958.4 | 1.46% | 0.685 | +0.00% | -2.41% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3031.6 | 0.64% | 0.696 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.35 | 10634.6 | 0.00% | 2162.0 | 13.25% | 0.500 | -0.00% | -0.22% | ff8b18c16b517923 |
| matvec-bands | 2.0.36 | 10634.6 | 0.00% | 2157.4 | 13.73% | 0.497 | -0.00% | -0.43% | ff8b18c16b517923 |
| matvec-bands | 2.0.37 | 10634.6 | 0.00% | 2149.6 | 12.01% | 0.495 | -0.00% | -0.79% | ff8b18c16b517923 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2247.0 | 15.98% | 0.511 | +0.00% | +3.71% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2166.7 | 10.64% | 0.505 |  |  | ff8b18c16b517923 |
| mnist-step | 2.0.35 | 22263.6 | 0.00% | 4843.9 | 0.92% | 1.106 | **+39.68%** | **+38.39%** | 2d83be930d21fb9f |
| mnist-step | 2.0.36 | 22124.2 | 0.00% | 4686.8 | 1.50% | 1.074 | **+38.80%** | **+33.90%** | 2d83be930d21fb9f |
| mnist-step | 2.0.37 | 22155.3 | 0.00% | 4685.8 | 1.53% | 1.075 | **+39.00%** | **+33.87%** | 2d83be930d21fb9f |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4582.2 | 1.54% | 1.061 | **+37.26%** | **+30.91%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3500.2 | 1.32% | 0.801 |  |  | 2d83be930d21fb9f |
| softmax-ce | 2.0.35 | 22363.7 | 0.00% | 7067.5 | 2.02% | 1.560 | **+186.01%** | **+181.40%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.36 | 21790.3 | 0.00% | 6861.0 | 0.90% | 1.515 | **+178.68%** | **+173.18%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.37 | 21883.2 | 0.00% | 6915.2 | 2.19% | 1.526 | **+179.86%** | **+175.34%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.38 | 22152.3 | 0.00% | 6829.2 | 1.23% | 1.518 | **+183.31%** | **+171.91%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2511.5 | 3.27% | 0.563 |  |  | debeda8b7bc50c1f |

## Beyond noise or differing outputs

- mnist-step: 2.0.35 instructions +39.68% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.35 cycles +38.39% against 2.0.39 (noise 1.32%)
- mnist-step: 2.0.36 instructions +38.80% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.36 cycles +33.90% against 2.0.39 (noise 1.50%)
- mnist-step: 2.0.37 instructions +39.00% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.37 cycles +33.87% against 2.0.39 (noise 1.53%)
- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +30.91% against 2.0.39 (noise 1.54%)
- softmax-ce: 2.0.35 instructions +186.01% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.35 cycles +181.40% against 2.0.39 (noise 3.27%)
- softmax-ce: 2.0.36 instructions +178.68% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.36 cycles +173.18% against 2.0.39 (noise 3.27%)
- softmax-ce: 2.0.37 instructions +179.86% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.37 cycles +175.34% against 2.0.39 (noise 3.27%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +171.91% against 2.0.39 (noise 3.27%)
