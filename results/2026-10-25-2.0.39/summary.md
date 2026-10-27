# 2026-10-25-2.0.39

Rounds per pair: 5. Changes are against Bend 2.0.39; **bold** is beyond noise (more than 3x the larger spread, floors 0.1% and 1%).

| workload | bend | Minstr | spread | Mcycles | spread | s | Δ instr | Δ cycles | hash |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| block-step | 2.0.38 | 31400.6 | 0.00% | 6102.9 | 1.03% | 1.375 | +0.00% | -0.17% | 4afdd96850039587 |
| block-step | 2.0.39 | 31400.6 | 0.00% | 6113.2 | 1.61% | 1.381 |  |  | 4afdd96850039587 |
| gemm-fork | 2.0.38 | 13906.9 | 0.00% | 2625.7 | 1.84% | 0.601 | +0.00% | +1.47% | 0c6d7fee9a7ddf37 |
| gemm-fork | 2.0.39 | 13906.9 | 0.00% | 2587.6 | 0.95% | 0.593 |  |  | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.38 | 13769.2 | 0.00% | 2975.9 | 0.91% | 0.670 | -0.00% | -1.60% | 0c6d7fee9a7ddf37 |
| gemm-tile8 | 2.0.39 | 13769.2 | 0.00% | 3024.3 | 5.55% | 0.678 |  |  | 0c6d7fee9a7ddf37 |
| matvec-bands | 2.0.38 | 10634.6 | 0.00% | 2266.3 | 14.93% | 0.516 | +0.00% | -0.27% | ff8b18c16b517923 |
| matvec-bands | 2.0.39 | 10634.6 | 0.00% | 2272.4 | 10.71% | 0.517 |  |  | ff8b18c16b517923 |
| mnist-step | 2.0.38 | 21878.3 | 0.00% | 4588.3 | 1.06% | 1.027 | **+37.26%** | **+31.45%** | 2d83be930d21fb9f |
| mnist-step | 2.0.39 | 15939.1 | 0.00% | 3490.5 | 2.47% | 0.778 |  |  | 2d83be930d21fb9f |
| softmax-ce | 2.0.38 | 22152.3 | 0.00% | 6756.5 | 2.86% | 1.491 | **+183.31%** | **+172.05%** | debeda8b7bc50c1f |
| softmax-ce | 2.0.39 | 7819.2 | 0.00% | 2483.6 | 4.23% | 0.555 |  |  | debeda8b7bc50c1f |

## Against the C targets (Bend 2.0.39 / C, medians)

| workload | C Minstr | C Mcycles | C s | instr ratio | cycles ratio | time ratio | same output |
|---|---:|---:|---:|---:|---:|---:|---|
| gemm-tile8 | 8121.9 | 2283.6 | 0.518 | 1.70x | 1.32x | 1.31x | yes |
| matvec-bands | 3258.5 | 1031.7 | 0.247 | 3.26x | 2.20x | 2.10x | yes |
| softmax-ce | 1603.0 | 511.8 | 0.124 | 4.88x | 4.85x | 4.46x | yes |

## Threads (wall time, medians; the output must be the same at every thread count)

| workload | bend | 1 thread s | 16 threads s | speedup | same output |
|---|---|---:|---:|---:|---|
| block-step | 2.0.38 | 1.375 | 0.309 | 4.45x | yes |
| block-step | 2.0.39 | 1.381 | 0.308 | 4.48x | yes |
| gemm-fork | 2.0.38 | 0.601 | 0.288 | 2.09x | yes |
| gemm-fork | 2.0.39 | 0.593 | 0.280 | 2.12x | yes |
| gemm-tile8 | 2.0.38 | 0.670 | 0.668 | 1.00x | yes |
| gemm-tile8 | 2.0.39 | 0.678 | 0.685 | 0.99x | yes |
| matvec-bands | 2.0.38 | 0.516 | 0.126 | 4.08x | yes |
| matvec-bands | 2.0.39 | 0.517 | 0.127 | 4.06x | yes |
| mnist-step | 2.0.38 | 1.027 | 0.992 | 1.03x | yes |
| mnist-step | 2.0.39 | 0.778 | 0.758 | 1.03x | yes |
| softmax-ce | 2.0.38 | 1.491 | 1.507 | 0.99x | yes |
| softmax-ce | 2.0.39 | 0.555 | 0.539 | 1.03x | yes |

## Beyond noise or differing outputs

- mnist-step: 2.0.38 instructions +37.26% against 2.0.39 (noise 0.10%)
- mnist-step: 2.0.38 cycles +31.45% against 2.0.39 (noise 2.47%)
- softmax-ce: 2.0.38 instructions +183.31% against 2.0.39 (noise 0.10%)
- softmax-ce: 2.0.38 cycles +172.05% against 2.0.39 (noise 4.23%)
