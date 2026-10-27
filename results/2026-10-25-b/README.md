# 2026-10-25-b: experiment 1 (plan v0, step 3)

Six workloads, Bend 2.0.35 to 2.0.39, 5 rounds, user-mode counts on CPU 3. Busy machine (load 2.7-3.8 from other
work): instructions are exact (spread 0.00%), cycles carry the load. `summary.md` is the table.

Finding: Bend 2.0.39 runs softmax-ce in 64.7% fewer instructions than 2.0.38 (22,152 -> 7,819 M) and mnist-step in
27.1% fewer (21,878 -> 15,939 M), cycles down by the same, the same bits. A walk of the 22 upstream commits between
the two tags (each built from source, `bun bend2/main.ts`) puts all of it on a5bae35c, bendlang/bend#1806 (fixes
#1805): a read-only walk over a `List<&2, F32>` stopped taking (owning) its list. That PR reports "Benches: identical
C"; the change it measured was a sort demo, 0.160 -> 0.122 s on one thread.
