# 2026-10-25-e: one and 16 threads (plan v1, step 1)

The six workloads on Bend 2.0.35-2.0.39 at 1 thread (pinned, counted) and 16 (unpinned, wall time), and the C
targets, 5 rounds; load 0.5 at the start, 2.3 at the end (other work started during it). `summary.md` has the tables. Every workload prints the same bytes at 1
and 16 threads on every version. Speedups at 16 threads on 2.0.39: block-step 4.42x, matvec-bands 4.12x, gemm-fork
2.19x (8 blocks), mnist-step 1.03x, softmax-ce 1.01x, gemm-tile8 1.00x (sequential by design); no version changed
them beyond a few percent.
