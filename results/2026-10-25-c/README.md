# 2026-10-25-c: the corpus with its C targets (plan v0, step 4)

The six workloads on Bend 2.0.35-2.0.39 and the three C targets, 5 rounds, user-mode counts on CPU 3, busy machine
(load ~2). `summary.md` is the table. The version findings repeat 2026-10-25-b to the instruction. Bend 2.0.39 against
C, the same bits in all three: gemm-tile8 1.32x cycles (1.70x instructions), matvec-bands 1.95x (3.26x), softmax-ce
4.83x (4.88x).
