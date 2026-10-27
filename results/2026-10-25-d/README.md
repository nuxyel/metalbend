# 2026-10-25-d: the quietest run (plan v0, step 2's conditions)

The six workloads and three C targets, 7 rounds, user-mode counts on CPU 3, on mains power in the `performance`
profile; load 0.8-1.0 (a browser open, nothing else running). Cycle spreads 0.5-3.5% (matvec-bands 3-8.6%, memory
bound). Instructions identical to 2026-10-25-b and -c. Bend 2.0.39 against C: gemm-tile8 1.33x cycles, matvec-bands
2.32x, softmax-ce 4.75x; Bend 2.0.39 against 2.0.38: softmax-ce -64% cycles, mnist-step -24%.
