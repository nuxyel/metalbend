# bpe-encode: instructions, v2.0.39 to v2.0.40

`git bisect` over bendlang/bend from v2.0.39 ([`a3efe8a3801f`](https://github.com/bendlang/bend/commit/a3efe8a3801f423827424227172eed9802c5e6cb)) to v2.0.40 ([`624dd9f4607c`](https://github.com/bendlang/bend/commit/624dd9f4607cd29b0871a9b96d413bfb11e92f52)), 118 commits, each step a source build of Bend and one Cachegrind count of the workload (`scripts/bisect.sh`; clang 18.1.3, valgrind 3.22.0). A commit is bad when its instructions are nearer the bad end's than the good end's; one that does not build or whose output is not its oracle is skipped.

**First bad commit:** [`0d35f6da9da0`](https://github.com/bendlang/bend/commit/0d35f6da9da0ab471c60c047c4c7bada4590e2fb) On Metal, the shared-node half of a take is a call, not code inlined into the taken match (#1978)
**Pull request:** [bendlang/bend#1978](https://github.com/bendlang/bend/pull/1978) On Metal, the shared-node half of a take is a call, not code inlined into the taken match
**Change:** instructions +7.84% at that commit (from its parent [`a346ded0e8aa`](https://github.com/bendlang/bend/commit/a346ded0e8aa1dd433c73db96856900c53e16214)), +9.42% over the whole range.

| | commit | instructions | D1 misses | output |
|---|---|---:|---:|---|
| good end | `a3efe8a3801f` | 195,728,925,870 | 1,108,191,529 | its oracle |
| parent | `a346ded0e8aa` | 195,828,416,010 | 1,108,191,151 | its oracle |
| first bad | `0d35f6da9da0` | 211,174,656,750 | 1,108,191,133 | its oracle |
| bad end | `624dd9f4607c` | 214,161,062,646 | 2,245,585,069 | its oracle |

## Steps

| # | commit | instructions | D1 misses | verdict | why |
|---:|---|---:|---:|---|---|
| 1 | `6a1f782a56cf` fix(demos): keep the sort and sum specs outside the editable programs  | 195,828,415,999 | 1,108,191,151 | good | instructions +0.05% from the good end (+9.42% at the bad end) |
| 2 | `3ca3df3209eb` fix(cli): reject colliding output requests before writing (#2010) | 211,174,656,750 | 1,108,191,133 | bad | instructions +7.89% from the good end (+9.42% at the bad end) |
| 3 | `1cecb123565d` fix(comp): C comments keep Unicode separators (#1972) | 195,828,416,010 | 1,108,191,151 | good | instructions +0.05% from the good end (+9.42% at the bad end) |
| 4 | `0d35f6da9da0` On Metal, the shared-node half of a take is a call, not code inlined i | 211,174,656,750 | 1,108,191,133 | bad | instructions +7.89% from the good end (+9.42% at the bad end) |
| 5 | `faeb02eaa164` fix(demos): app_triangle_2d's click laws read the triangle from SPEC.b | 195,828,416,010 | 1,108,191,151 | good | instructions +0.05% from the good end (+9.42% at the bad end) |
| 6 | `e9d269b588f4` fix(io): a JS File.read's max is a cap, not its buffer size (#1983) (# | 195,828,416,010 | 1,108,191,151 | good | instructions +0.05% from the good end (+9.42% at the bad end) |
| 7 | `a346ded0e8aa` perf(js): avoid backtracking in GPU size validation (#1993) | 195,828,416,010 | 1,108,191,151 | good | instructions +0.05% from the good end (+9.42% at the bad end) |

## Per function, parent to first bad commit (Cachegrind, instructions)

The functions that changed, largest first; together +15,346,240,740. A function carrying at least 5% of that is marked.

| function | parent | commit | change | share | |
|---|---:|---:|---:|---:|---|
| `span_fade` | 1,105,924,400 | 28,054,477,916 | +26,948,553,516 | 175.6% | moved |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go` | 86,331,217,798 | 76,121,353,272 | -10,209,864,526 | -66.5% | moved |
| `spin_0x559a0abb492a951db15be435191b6d0a_main_peek` | 3,833,955,846 | 2,895,074,381 | -938,881,465 | -6.1% | moved |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go` | 4,997,682,282 | 4,607,126,542 | -390,555,740 | -2.5% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go` | 355,392,115 | 299,193,800 | -56,198,315 | -0.4% |  |
| `spin_0x559a0abb492a951db15be435191b6d0a_main_best` | 25,411,314 | 20,898,285 | -4,513,029 | -0.0% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_lift` | 9,327,761 | 7,502,726 | -1,825,035 | -0.0% |  |
| `WL_FID_main_k9` | 2,783,794 | 2,307,446 | -476,348 | -0.0% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_encode_go` | 28,941 | 30,729 | +1,788 | 0.0% |  |
| `io_cbuf` | 966 | 876 | -90 | -0.0% |  |
| `io_loop` | 414 | 398 | -16 | -0.0% |  |

All of them: `functions.tsv`.

## The emitted C, parent to first bad commit

Definitions whose text differs (lines added, removed): `(outside any function)` (+1 -0), `ctr_take` (+3 -14), `span_fade` (+8 -1).

```diff
--- parent/span_fade
+++ commit/span_fade
@@ -1,3 +1,9 @@
-OUTLINE void span_fade(Env e, Term t, u64 src, u32 n) {
+FAR u64 span_fade(Env e, Term t, u64 src, u32 n) {
+  DEV u32* c = a32_at(e.mem, term_loc(t));
+  if ((a32_load(c) & RFC_CNT) == 1) {
+    a32_acq(c);
+    heap_free(e, 0, term_loc(t));
+    return src;
+  }
   for (u32 j = 0; j < n; j += 1) {
     Term f = e.mem[src + j];
@@ -9,3 +15,4 @@
   }
   term_drop(e, t);
+  return 0;
 }
--- parent/(outside any function)
+++ commit/(outside any function)
@@ -645,4 +645,5 @@
 
 
+// Inlined, M1 Metal runs wrong (#1954).
 
 
--- parent/ctr_take
+++ commit/ctr_take
@@ -1,18 +1,7 @@
 INLINE u64 ctr_take(Env e, Term t, u32 n, THR Term* out) {
-  DEV u64* H = e.mem;
-  u64 src = term_peek(H, t);
+  u64 src = term_peek(e.mem, t);
   for (u32 j = 0; j < n; j += 1) {
-    out[j] = H[src + j];
+    out[j] = e.mem[src + j];
   }
-  if (!term_rfc(t)) {
-    return src;
-  }
-  DEV u32* c = a32_at(H, term_loc(t));
-  if ((a32_load(c) & RFC_CNT) == 1) {
-    a32_acq(c);
-    heap_free(e, 0, term_loc(t));
-    return src;
-  }
-  span_fade(e, t, src, n);
-  return 0;
+  return term_rfc(t) ? span_fade(e, t, src, n) : src;
 }
```
The whole file's diff: `c.diff`.

## Again

From a clone of this repository (bun, clang and valgrind on PATH):

```sh
make data
scripts/count.sh a346ded0e8aa bpe-encode
scripts/count.sh 0d35f6da9da0 bpe-encode
scripts/bisect.sh bpe-encode v2.0.39 v2.0.40 ir
```

The run: https://github.com/nuxyel/metalbend/actions/runs/42384646460.
