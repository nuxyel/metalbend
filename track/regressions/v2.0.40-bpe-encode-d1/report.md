# bpe-encode: D1 misses, v2.0.39 to v2.0.40

`git bisect` over bendlang/bend from v2.0.39 ([`a3efe8a3801f`](https://github.com/bendlang/bend/commit/a3efe8a3801f423827424227172eed9802c5e6cb)) to v2.0.40 ([`624dd9f4607c`](https://github.com/bendlang/bend/commit/624dd9f4607cd29b0871a9b96d413bfb11e92f52)), 118 commits, each step a source build of Bend and one Cachegrind count of the workload (`scripts/bisect.sh`; clang 18.1.3, valgrind 3.22.0). A commit is bad when its D1 misses are nearer the bad end's than the good end's; one that does not build or whose output is not its oracle is skipped.

**First bad commit:** [`3c1f0d3a0937`](https://github.com/bendlang/bend/commit/3c1f0d3a0937aaae164963eefb12065a6ac369ad) perf(comp): a wide def's boxed record stays boxed until a use needs it (#2036)
**Pull request:** [bendlang/bend#2036](https://github.com/bendlang/bend/pull/2036) perf(comp): a wide def's boxed record stays boxed until a use needs it
**Change:** D1 misses 2.03x at that commit (from its parent [`4024f04dc655`](https://github.com/bendlang/bend/commit/4024f04dc65527d9783481ba0672b818039c80d1)), 2.03x over the whole range.

| | commit | instructions | D1 misses | output |
|---|---|---:|---:|---|
| good end | `a3efe8a3801f` | 195,728,925,870 | 1,108,191,529 | its oracle |
| parent | `4024f04dc655` | 211,174,656,755 | 1,108,191,133 | its oracle |
| first bad | `3c1f0d3a0937` | 214,161,062,646 | 2,245,585,069 | its oracle |
| bad end | `624dd9f4607c` | 214,161,062,646 | 2,245,585,069 | its oracle |

## Steps

| # | commit | instructions | D1 misses | verdict | why |
|---:|---|---:|---:|---|---|
| 1 | `6a1f782a56cf` fix(demos): keep the sort and sum specs outside the editable programs  | 195,828,415,999 | 1,108,191,151 | good | D1 misses -0.00% from the good end (2.03x at the bad end) |
| 2 | `3ca3df3209eb` fix(cli): reject colliding output requests before writing (#2010) | 211,174,656,750 | 1,108,191,133 | good | D1 misses -0.00% from the good end (2.03x at the bad end) |
| 3 | `2534c1555cfa` perf(c): blk_new fills whole elements, clones keep runs; JS shares the | 211,174,656,755 | 1,108,191,133 | good | D1 misses -0.00% from the good end (2.03x at the bad end) |
| 4 | `c8dde1eeece5` perf(comp): an unfold builds the callee's body once (#2051) | 214,161,062,646 | 2,245,585,069 | bad | D1 misses 2.03x from the good end (2.03x at the bad end) |
| 5 | `3c1f0d3a0937` perf(comp): a wide def's boxed record stays boxed until a use needs it | 214,161,062,646 | 2,245,585,069 | bad | D1 misses 2.03x from the good end (2.03x at the bad end) |
| 6 | `4024f04dc655` fix(demos): app_slash_boss_3d's frame loop counts down a fuel, so its  | 211,174,656,755 | 1,108,191,133 | good | D1 misses -0.00% from the good end (2.03x at the bad end) |

## Per function, parent to first bad commit (Cachegrind, D1 misses)

The functions that changed, largest first; together +1,137,393,936. A function carrying at least 5% of that is marked.

| function | parent | commit | change | share | |
|---|---:|---:|---:|---:|---|
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go` | 535,538,218 | 1,087,995,730 | +552,457,512 | 48.6% | moved |
| `rfc_wrap` | 61,092,113 | 453,926,156 | +392,834,043 | 34.5% | moved |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go_k1` | 472,672,664 | 637,403,989 | +164,731,325 | 14.5% | moved |
| `span_fade` | 7,010,168 | 29,476,394 | +22,466,226 | 2.0% |  |
| `spin_0x559a0abb492a951db15be435191b6d0a_main_peek` | 5,649,119 | 14,303,903 | +8,654,784 | 0.8% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go_k3` | 14,931,640 | 9,119,152 | -5,812,488 | -0.5% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go` | 2,017,761 | 5,203,485 | +3,185,724 | 0.3% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go` | 6,558,059 | 4,419,926 | -2,138,133 | -0.2% |  |
| `spin_0x559a0abb492a951db15be435191b6d0a_main_best` | 322,099 | 634,920 | +312,821 | 0.0% |  |
| `term_drop` | 649,953 | 870,244 | +220,291 | 0.0% |  |
| `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump` | 639,892 | 855,603 | +215,711 | 0.0% |  |
| `WL_FID_main_k9` | 20,527 | 94,311 | +73,784 | 0.0% |  |
| 16 more | | | | | |

All of them: `functions.tsv`.

## The emitted C, parent to first bad commit

Definitions whose text differs (lines added, removed): `(top-level)` (+1 -1), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go` (+2 -2), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go` (+42 -47), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1` (+8 -20), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go` (+40 -108), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go_k3` (+6 -18), `WL_FID_0x559a0abb492a951db15be435191b6d0a_main_merge_go_k5` (+6 -18), `spin_0x559a0abb492a951db15be435191b6d0a_main_peek` (+39 -38).

```diff
--- parent/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go
+++ commit/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_bump_go
@@ -32,7 +32,6 @@
       Term _f_5 = _fb_1[3];
       Term _f_6 = _fb_1[4];
-      spare_free(e, cls_fit(5), _sp_1);
       if (_hit_0 == 1) {
-        u64 _nd_2 = heap_alloc(e, 3);
+        u64 _nd_2 = _sp_1 >= HEAP_OFF ? _sp_1 : heap_alloc(e, 3);
         e.mem[_nd_2 + 0] = rfc_seal(e, _f_2);
         e.mem[_nd_2 + 1] = rfc_seal(e, _f_3);
@@ -50,4 +49,5 @@
           return 0;
         }
+        spare_free(e, cls_fit(5), _sp_1);
         spare_free(e, cls_fit(2), _sp_0);
         if (seq) {
--- parent/(top-level)
+++ commit/(top-level)
@@ -385,5 +385,5 @@
 #define FID_EXIT 45
 #define FID_ENTER 46
-CONSTV Fid FID_T[] = { { 3, 0, 0, 1 }, { 6, 0, 0, 1 }, { 6, 1, 0, 1 }, { 8, 0, 0, 1 }, { 3, 1, 0, 1 }, { 3, 1, 0, 1 }, { 3, 1, 0, 1 }, { 5, 0, 0, 1 }, { 7, 0, 0, 1 }, { 2, 0, 0, 1 }, { 2, 1, 0, 1 }, { 1, 0, 0, 1 }, { 3, 0, 0, 1 }, { 3, 0, 0, 1 }, { 2, 1, 0, 1 }, { 1, 0, 0, 1 }, { 2, 1, 0, 1 }, { 2, 0, 0, 1 }, { 4, 1, 0, 1 }, { 9, 0, 0, 1 }, { 7, 1, 0, 1 }, { 8, 1, 0, 1 }, { 6, 1, 0, 1 }, { 2, 0, 0, 1 }, { 1, 0, 0, 1 }, { 1, 1, 0, 1 }, { 2, 0, 0, 1 }, { 3, 0, 0, 1 }, { 4, 1, 0, 1 }, { 0, 0, 0, 1 }, { 1, 1, 0, 1 }, { 1, 1, 0, 1 }, { 2, 1, 0, 1 }, { 3, 1, 0, 1 }, { 2, 1, 0, 1 }, { 3, 1, 0, 1 }, { 4, 0, 0, 1 }, { 3, 0, 0, 1 }, { 2, 1, 0, 1 }, { 3, 0, 0, 1 }, { 2, 0, 0, 1 }, { 1, 1, 0, 1 }, { 2, 0, 0, 1 }, { 1, 0, 0, 1 }, { 2, 0, 0, 1 } };
+CONSTV Fid FID_T[] = { { 3, 0, 0, 1 }, { 6, 0, 0, 1 }, { 6, 1, 0, 1 }, { 8, 0, 0, 1 }, { 3, 1, 0, 1 }, { 2, 1, 0, 1 }, { 2, 1, 0, 1 }, { 5, 0, 0, 1 }, { 7, 0, 0, 1 }, { 2, 0, 0, 1 }, { 2, 1, 0, 1 }, { 1, 0, 0, 1 }, { 3, 0, 0, 1 }, { 3, 0, 0, 1 }, { 2, 1, 0, 1 }, { 1, 0, 0, 1 }, { 2, 1, 0, 1 }, { 2, 0, 0, 1 }, { 3, 1, 0, 1 }, { 9, 0, 0, 1 }, { 7, 1, 0, 1 }, { 8, 1, 0, 1 }, { 6, 1, 0, 1 }, { 2, 0, 0, 1 }, { 1, 0, 0, 1 }, { 1, 1, 0, 1 }, { 2, 0, 0, 1 }, { 3, 0, 0, 1 }, { 4, 1, 0, 1 }, { 0, 0, 0, 1 }, { 1, 1, 0, 1 }, { 1, 1, 0, 1 }, { 2, 1, 0, 1 }, { 3, 1, 0, 1 }, { 2, 1, 0, 1 }, { 3, 1, 0, 1 }, { 4, 0, 0, 1 }, { 3, 0, 0, 1 }, { 2, 1, 0, 1 }, { 3, 0, 0, 1 }, { 2, 0, 0, 1 }, { 1, 1, 0, 1 }, { 2, 0, 0, 1 }, { 1, 0, 0, 1 }, { 2, 0, 0, 1 } };
 CONSTV Cid CID_T[] = { { 2, 0, 0 }, { 0, 0, 0 }, { 2, 0, 0 }, { 2, 0, 0 }, { 1, 0, 0 }, { 2, 0, 0 }, { 1, 0, 0 }, { 1, 0, 0 }, { 1, 0, 0 }, { 1, 0, 0 }, { 1, 0, 0 }, { 0, 0, 0 }, { 1, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 }, { 1, 0, 0 }, { 0, 1, 0 }, { 2, 1, 0 }, { 5, 1, 0 }, { 1, 1, 0 }, { 1, 1, 0 }, { 5, 1, 0 }, { 0, 0, 0 }, { 0, 0, 0 }, { 0, 0, 0 }, { 2, 0, 0 } };
 #define STAT_LEN 2
--- parent/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go
+++ commit/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go
@@ -11,78 +11,73 @@
       Term _f_0 = _fb_0[0];
       Term _f_1 = _fb_0[1];
-      u32 _o_0 = 0;
-      Term _o_1 = 0;
-      if (term_aux(_f_0) == CID_0x559a0abb492a951db15be435191b6d0a_main_B) {
-        _o_0 = 0;
-        Term _fb_1[1];
-        u64 _sp_1 = ctr_take(e, _f_0, 1, _fb_1);
-        Term _f_2 = _fb_1[0];
-        spare_free(e, cls_fit(1), _sp_1);
-        _o_1 = _f_2;
-      } else {
-        _o_0 = 1;
-        Term _fb_2[1];
-        u64 _sp_2 = ctr_take(e, _f_0, 1, _fb_2);
-        Term _f_3 = _fb_2[0];
-        spare_free(e, cls_fit(1), _sp_2);
-        _o_1 = _f_3;
-      }
       if (term_aux(_f_1) == CID_Nil) {
+        term_sink(e, _f_0);
         spare_free(e, cls_fit(2), _sp_0);
         r0 = _cs_0;
         WL_RETN(1);
       } else {
-        Term _fb_3[2];
-        u64 _sp_3 = ctr_take(e, _f_1, 2, _fb_3);
-        Term _f_4 = _fb_3[0];
-        Term _f_5 = _fb_3[1];
+        Term _fb_1[2];
+        u64 _sp_1 = ctr_take(e, _f_1, 2, _fb_1);
+        Term _f_2 = _fb_1[0];
+        Term _f_3 = _fb_1[1];
+        u32 _o_0 = 0;
+        Term _o_1 = 0;
+        if (term_aux(_f_2) == CID_0x559a0abb492a951db15be435191b6d0a_main_B) {
+          _o_0 = 0;
+          u64 _sp_2 = term_peek(e.mem, _f_2);
+          Term _f_4 = e.mem[_sp_2 + 0];
+          _o_1 = _f_4;
+        } else {
+          _o_0 = 1;
+          u64 _sp_3 = term_peek(e.mem, _f_2);
+          Term _f_5 = e.mem[_sp_3 + 0];
+          _o_1 = _f_5;
+        }
         u32 _o_2 = 0;
         Term _o_3 = 0;
-        if (term_aux(_f_4) == CID_0x559a0abb492a951db15be435191b6d0a_main_B) {
+        if (term_aux(_f_0) == CID_0x559a0abb492a951db15be435191b6d0a_main_B) {
           _o_2 = 0;
-          Term _fb_4[1];
-          u64 _sp_4 = ctr_take(e, _f_4, 1, _fb_4);
-          Term _f_6 = _fb_4[0];
+          Term _fb_2[1];
+          u64 _sp_4 = ctr_take(e, _f_0, 1, _fb_2);
+          Term _f_6 = _fb_2[0];
           spare_free(e, cls_fit(1), _sp_4);
           _o_3 = _f_6;
         } else {
           _o_2 = 1;
-          Term _fb_5[1];
-          u64 _sp_5 = ctr_take(e, _f_4, 1, _fb_5);
-          Term _f_7 = _fb_5[0];
+          Term _fb_3[1];
+          u64 _sp_5 = ctr_take(e, _f_0, 1, _fb_3);
+          Term _f_7 = _fb_3[0];
           spare_free(e, cls_fit(1), _sp_5);
           _o_3 = _f_7;
         }
-        spare_free(e, cls_fit(2), _sp_3);
+        spare_free(e, cls_fit(2), _sp_1);
         spare_free(e, cls_fit(2), _sp_0);
         if (seq) {
-          WL_ROOM(4);
-          STK(0) = _o_2;
-          STK(1) = _o_3;
-          STK(2) = _f_5;
-          STK(3) = FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1;
-          WL_PUSHN(4);
+          WL_ROOM(3);
+          STK(0) = _f_2;
+          STK(1) = _f_3;
+          STK(2) = FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1;
+          WL_PUSHN(3);
         } else {
           u64 _t_0 = task_node(e, FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1, WL_CONT, WL_IDX, 1);
-          e.mem[_t_0 + 0] = _o_2;
-          e.mem[_t_0 + 1] = _o_3;
-          e.mem[_t_0 + 2] = _f_5;
+          e.mem[_t_0 + 0] = _f_2;
+          e.mem[_t_0 + 1] = _f_3;
           WL_CONT = term_tsk(FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1, _t_0);
-          WL_IDX = 3;
+          WL_IDX = 2;
         }
         if (!DEVICE && !seq && fid_nofk(FID_0x559a0abb492a951db15be435191b6d0a_main_bump)) {
           u64 _t_1 = task_node(e, FID_0x559a0abb492a951db15be435191b6d0a_main_bump, WL_CONT, WL_IDX, 0);
           e.mem[_t_1 + 0] = _cs_0;
-          e.mem[_t_1 + 1] = _o_0;
-          e.mem[_t_1 + 2] = _o_1;
-          e.mem[_t_1 + 3] = _o_2;
-          e.mem[_t_1 + 4] = _o_3;
+          e.mem[_t_1 + 1] = _o_2;
+          e.mem[_t_1 + 2] = _o_3;
+          e.mem[_t_1 + 3] = _o_0;
+          e.mem[_t_1 + 4] = _o_1;
           return term_tsk(FID_0x559a0abb492a951db15be435191b6d0a_main_bump, _t_1);
         }
         r0 = _cs_0;
-        r1 = _o_0;
-        r2 = _o_1;
-        r3 = _o_2;
-        r4 = _o_3;
+        r1 = _o_2;
+        r2 = _o_3;
+        r3 = _o_0;
+        r4 = _o_1;
         WL_JMP(FID_0x559a0abb492a951db15be435191b6d0a_main_bump);
       }
--- parent/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1
+++ commit/WL_FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1
@@ -1,30 +1,18 @@
   WL_CASE(FID_0x559a0abb492a951db15be435191b6d0a_main_count_go_k1)
-    WL_POPN(3);
-    u32 _o_4 = STK(0);
-    Term _o_5 = STK(1);
-    Term _f_8 = STK(2);
+    WL_POPN(2);
+    Term _f_8 = STK(0);
+    Term _f_9 = STK(1);
```
385 more lines in `c.diff`, the whole file's diff.

## Again

From a clone of this repository (bun, clang and valgrind on PATH):

```sh
make data
scripts/count.sh 4024f04dc655 bpe-encode
scripts/count.sh 3c1f0d3a0937 bpe-encode
scripts/bisect.sh bpe-encode v2.0.39 v2.0.40 d1
```

The run: https://github.com/nuxyel/metalbend/actions/runs/42384646460.
