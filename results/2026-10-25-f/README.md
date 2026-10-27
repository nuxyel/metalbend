# 2026-10-25-f: eleven workloads (plan v1, step 3)

The six of plan v0 and five new ones (attention-step, rmsnorm-step, adamw, read-native, read-binary) on Bend
2.0.35-2.0.39 at 1 and 16 threads, five C targets, 5 rounds; load ~1-1.4. `summary.md` has the tables.

- Every workload prints the same bytes on every version that builds it and at 1 and 16 threads. read-binary does not
  build on 2.0.35 (bend-ml-binary-read 0.2.0.0's C effect calls the runtime's `io_eff` with 2.0.36's three
  arguments); recorded, not fixed.
- The new workloads moved by no version beyond noise (instructions within 0.02%).
- Bend 2.0.39 / C in cycles: adamw 1.20x, mnist-step 1.96x, read-native 21x in user mode (6.1x in wall time; the
  kernel's read is not counted), next to gemm-tile8 1.32x, matvec-bands 2.27x, softmax-ce 4.79x. read-binary takes
  20.8 M user cycles against the C read's 17.2 M.
- At 16 threads: attention-step 3.7x; adamw, rmsnorm-step and the reads 0.7-1.0x (sequential loops, and at 16 threads
  the reads lose to the start-up of the workers).
