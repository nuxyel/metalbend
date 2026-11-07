# gemm-fork: instructions, v2.0.32 to v2.0.33

`git bisect` over bendlang/bend from v2.0.32 ([`573002f01ec6`](https://github.com/bendlang/bend/commit/573002f01ec6c52416d44489543f69a9625facf8)) to v2.0.33 ([`c05efd9570d5`](https://github.com/bendlang/bend/commit/c05efd9570d542b433b4762ba2978e0177708e5f)), 24 commits, each step a source build of Bend and one Cachegrind count of the workload (`scripts/bisect.sh`; clang 18.1.3, valgrind 3.22.0). A commit is bad when its instructions are nearer the bad end's than the good end's; one that does not build or whose output is not its oracle is skipped.

**First bad commit:** [`ef66a7ccf5d0`](https://github.com/bendlang/bend/commit/ef66a7ccf5d0d48478f33736a4c5bef48d439e74) A shared Array's redirect is read without a race and without an atomic on the device, once per spin (#1155)
**Pull request:** [bendlang/bend#1155](https://github.com/bendlang/bend/pull/1155) A shared Array's redirect is read without a race and without an atomic on the device, once per spin (#975)
**Change:** instructions 0.26x at that commit (from its parent [`6de56b973213`](https://github.com/bendlang/bend/commit/6de56b973213b3cbea0cebcf1fe82a482d75181a)), 0.26x over the whole range.

| | commit | instructions | D1 misses | output |
|---|---|---:|---:|---|
| good end | `573002f01ec6` | 50,696,482,359 | 358,952,505 | its oracle |
| parent | `6de56b973213` | 50,696,482,335 | 358,952,505 | its oracle |
| first bad | `ef66a7ccf5d0` | 13,321,507,673 | 358,850,796 | its oracle |
| bad end | `c05efd9570d5` | 13,321,507,671 | 358,850,796 | its oracle |

## Steps

| # | commit | instructions | D1 misses | verdict | why |
|---:|---|---:|---:|---|---|
| 1 | `cb029ebe7bc4` Update README.md | 13,321,507,673 | 358,850,796 | bad | instructions 0.26x from the good end (0.26x at the bad end) |
| 2 | `a0627e0a1de0` Effects build their Result through io_res, one macro in the Io section | 50,696,482,359 | 358,952,505 | good | instructions +0.00% from the good end (0.26x at the bad end) |
| 3 | `ef66a7ccf5d0` A shared Array's redirect is read without a race and without an atomic | 13,321,507,673 | 358,850,796 | bad | instructions 0.26x from the good end (0.26x at the bad end) |
| 4 | `6de56b973213` Base says the same with fewer helpers, and U32.log2 takes five native  | 50,696,482,335 | 358,952,505 | good | instructions -0.00% from the good end (0.26x at the bad end) |

## Per function, parent to first bad commit (Cachegrind, instructions)

The functions that changed, largest first; together -37,374,974,662. A function carrying at least 5% of that is marked.

| function | parent | commit | change | share | |
|---|---:|---:|---:|---:|---|
| `spin_8` | 49,132,437,504 | 0 | -49,132,437,504 | 131.5% | moved |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR` | 913,232 | 8,327,269,856 | +8,326,356,624 | -22.3% | moved |
| `spin_26` | 0 | 4,345,999,104 | +4,345,999,104 | -11.6% | moved |
| `spin_24` | 595,267,584 | 0 | -595,267,584 | 1.6% |  |
| `spin_20` | 547,990,528 | 251,501,824 | -296,488,704 | 0.8% |  |
| `WL_FID_______LIB_TA_SHOW_C` | 29,933,805 | 7,127,280 | -22,806,525 | 0.1% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_RPAR` | 370,360 | 17,712 | -352,648 | 0.0% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0` | 61,200 | 71,952 | +10,752 | -0.0% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0_J54` | 20,160 | 27,552 | +7,392 | -0.0% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR_J58` | 4,144 | 5,376 | +1,232 | -0.0% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0_K54` | 26,544 | 27,216 | +672 | -0.0% |  |
| `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_RPAR_J62` | 2,072 | 2,688 | +616 | -0.0% |  |
| 10 more | | | | | |

All of them: `functions.tsv`.

## The emitted C, parent to first bad commit

Definitions whose text differs (lines added, removed): `(outside any function)` (+4 -2), `WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_PK_PACK_K99` (+2 -1), `WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_PK_TREE_K68` (+3 -2), `WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_T8_CPAR` (+6 -5), `WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_T8_RPAR` (+6 -5), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0` (+7 -7), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0_J54` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_BLOCKS2_0_K54` (+2 -2), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR` (+11 -11), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR_J58` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR_K58` (+3 -3), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_GEMM_ANY` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_GEMM_ANY_K180` (+2 -2), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_GEMM_ANY_K183` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_GEMM_ANY_K186` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_GEMM_ANY_K188` (+4 -4), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_PAR2_0` (+2 -2), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_PK_PAR_K104` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_RPAR` (+10 -10), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_RPAR_J62` (+1 -1), `WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_RPAR_K62` (+3 -3), `WL_FID_______LIB_GEMM_FORK_NN_STEP_K207` (+1 -1), `WL_FID_______LIB_GEMM_FORK_NT_STEP_K214` (+1 -1), `WL_FID_______LIB_GEMM_FORK_TN_STEP_K209` (+1 -1), `WL_FID_______LIB_TA_RMAT_K224` (+1 -1), `WL_FID_______LIB_TA_SHOW_C` (+1 -1), `blk_loc` (+1 -1), `spin_1` (+4 -2), `spin_10` (+3 -1), `spin_13` (+5 -3), `spin_14` (+4 -2), `spin_15` (+5 -2), `spin_16` (+4 -2), `spin_17` (+3 -1), `spin_18` (+5 -3), `spin_2` (+5 -3), `spin_20` (+4 -2), `spin_21` (+5 -3), `spin_22` (+5 -3), `spin_23` (+3 -1), `spin_24` (+6 -3), `spin_25` (+5 -2), `spin_26` (+5 -2), `spin_27` (+4 -1), `spin_28` (+6 -3), `spin_29` (+5 -2), `spin_3` (+5 -3), `spin_30` (+4 -4), `spin_31` (+3 -1), `spin_32` (+4 -2), `spin_33` (+5 -3), `spin_34` (+2 -1), `spin_35` (+2 -1), `spin_36` (+7 -3), `spin_37` (+3 -1), `spin_38` (+3 -1), `spin_39` (+5 -2), `spin_4` (+5 -3), `spin_40` (+6 -3), `spin_41` (+4 -2), `spin_42` (+3 -1), `spin_43` (+4 -2), `spin_45` (+6 -1), `spin_5` (+5 -3), `spin_50` (+3 -1), `spin_51` (+3 -1), `spin_52` (+5 -1), `spin_53` (+8 -3), `spin_54` (+5 -3), `spin_55` (+4 -2), `spin_56` (+1 -1), `spin_57` (+9 -6), `spin_58` (+8 -5), `spin_6` (+5 -4), `spin_62` (+5 -2), `spin_69` (+4 -1), `spin_7` (+3 -2), `spin_70` (+4 -1), `spin_71` (+3 -2), `spin_72` (+4 -1), `spin_73` (+3 -2), `spin_75` (+3 -2), `spin_76` (+4 -3), `spin_77` (+3 -2), `spin_8` (+7 -5), `spin_9` (+5 -3).

```diff
--- parent/WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR
+++ commit/WL_FID_0XD13098B0F80022977B3DDB83A57E3C50_MAIN_CPAR
@@ -29,5 +29,5 @@
       Term _v_5 = 0;
       Term _o_1[3];
-      if (spin_39(e, _o_1, _ac_0, _n_0, _cnt_0, _tk_0, _tku_0, _rot_0, 0ull, _j0_0, _mu_0, _pa_0, _pb_0, _pc_0) == 0) {
+      if (spin_39(e, _o_1, _ac_0, _n_0, _cnt_0, _tk_0, _tku_0, _rot_0, 0ull, _j0_0, _mu_0, _pa_0, blk_loc(e.mem, _pa_0), _pb_0, blk_loc(e.mem, _pb_0), _pc_0, blk_loc(e.mem, _pc_0)) == 0) {
         return 0;
       }
@@ -40,5 +40,5 @@
       Term _v_15 = 0;
       Term _o_2[1];
-      if (spin_27(e, _o_2, _v_0, _v_1, _v_2) == 0) {
+      if (spin_27(e, _o_2, _v_0, blk_loc(e.mem, _v_0), _v_1, blk_loc(e.mem, _v_1), _v_2, blk_loc(e.mem, _v_2)) == 0) {
         return 0;
       }
@@ -62,5 +62,5 @@
         Term _v_21 = 0;
         Term _o_4[2];
-        if (spin_35(e, _o_4, _pa_0) == 0) {
+        if (spin_35(e, _o_4, _pa_0, blk_loc(e.mem, _pa_0)) == 0) {
           return 0;
         }
@@ -74,5 +74,5 @@
         Term _v_25 = 0;
         Term _o_5[2];
-        if (spin_35(e, _o_5, _pb_0) == 0) {
+        if (spin_35(e, _o_5, _pb_0, blk_loc(e.mem, _pb_0)) == 0) {
           return 0;
         }
@@ -86,5 +86,5 @@
         Term _v_29 = 0;
         Term _o_6[2];
-        if (spin_34(e, _o_6, _pc_0) == 0) {
+        if (spin_34(e, _o_6, _pc_0, blk_loc(e.mem, _pc_0)) == 0) {
           return 0;
         }
@@ -114,5 +114,5 @@
         Term _v_37 = 0;
         Term _o_9[2];
-        if (spin_35(e, _o_9, _pa_1) == 0) {
+        if (spin_35(e, _o_9, _pa_1, blk_loc(e.mem, _pa_1)) == 0) {
           return 0;
         }
@@ -126,5 +126,5 @@
         Term _v_41 = 0;
         Term _o_10[2];
-        if (spin_35(e, _o_10, _pb_1) == 0) {
+        if (spin_35(e, _o_10, _pb_1, blk_loc(e.mem, _pb_1)) == 0) {
           return 0;
         }
@@ -138,5 +138,5 @@
         Term _v_45 = 0;
         Term _o_11[2];
-        if (spin_34(e, _o_11, _pc_1) == 0) {
+        if (spin_34(e, _o_11, _pc_1, blk_loc(e.mem, _pc_1)) == 0) {
           return 0;
         }
@@ -195,5 +195,5 @@
       Term _v_51 = 0;
       Term _o_13[2];
-      if (spin_35(e, _o_13, _pa_0) == 0) {
+      if (spin_35(e, _o_13, _pa_0, blk_loc(e.mem, _pa_0)) == 0) {
         return 0;
       }
@@ -207,5 +207,5 @@
       Term _v_55 = 0;
       Term _o_14[2];
-      if (spin_35(e, _o_14, _pb_0) == 0) {
+      if (spin_35(e, _o_14, _pb_0, blk_loc(e.mem, _pb_0)) == 0) {
         return 0;
       }
@@ -219,5 +219,5 @@
       Term _v_59 = 0;
       Term _o_15[2];
-      if (spin_34(e, _o_15, _pc_0) == 0) {
+      if (spin_34(e, _o_15, _pc_0, blk_loc(e.mem, _pc_0)) == 0) {
         return 0;
       }
--- parent/spin_26
+++ commit/spin_26
@@ -1,4 +1,7 @@
-INLINE Term spin_26(Env e, THR Term* o, u32 r0, Term r1, Term r2, Term r3, u32 r4, Term r5, u32 r6, u32 r7, Term r8, Term r9, Term r10) {
+INLINE Term spin_26(Env e, THR Term* o, u32 r0, Term r1, Term r2, Term r3, u32 r4, Term r5, u32 r6, u32 r7, Term r8, u64 q8, Term r9, u64 q9, Term r10, u64 q10) {
   u32 wpoll = 0;
+  Term h8 = r8;
+  Term h9 = r9;
+  Term h10 = r10;
   Term _v_6 = 0;
   Term _v_7 = 0;
@@ -29,5 +32,5 @@
       Term _v_14 = 0;
       Term _o_0[3];
-      if (spin_24(e, _o_0, _ac_1, _m_1, _tk_1, _tku_1, _rot_1, _i_0, 0ull, U32_BIN(_i_0, *, _mu_1), _g_0, _g_1, _g_2) == 0) {
+      if (spin_24(e, _o_0, _ac_1, _m_1, _tk_1, _tku_1, _rot_1, _i_0, 0ull, U32_BIN(_i_0, *, _mu_1), _g_0, _g_0 == h8 ? q8 : blk_loc(e.mem, _g_0), _g_1, _g_1 == h9 ? q9 : blk_loc(e.mem, _g_1), _g_2, _g_2 == h10 ? q10 : blk_loc(e.mem, _g_2)) == 0) {
         return 0;
       }
--- parent/spin_8
+++ commit/spin_8
@@ -1,4 +1,6 @@
-INLINE Term spin_8(Env e, THR Term* o, Term r0, u32 r1, Term r2, u32 r3, u32 r4, Term r5, Term r6) {
+INLINE Term spin_8(Env e, THR Term* o, Term r0, u32 r1, Term r2, u32 r3, u32 r4, Term r5, u64 q5, Term r6, u64 q6) {
   u32 wpoll = 0;
+  Term h5 = r5;
+  Term h6 = r6;
   Term _v_6 = 0;
   Term _v_7 = 0;
@@ -18,5 +20,5 @@
     u32 _v_13 = 0;
     u32 _v_14 = 0;
-    Term _at_0 = blk_loc(e.mem, _a_0);
+    Term _at_0 = _a_0 == h5 ? q5 : blk_loc(e.mem, _a_0);
     Term _at_1 = blk_at(_a_0, U32_BIN(_i_1, *, _tku_1), 3);
     u32 _c_0 = blk_read(e.mem, 0, _at_0, _at_1 + 0);
@@ -28,5 +30,5 @@
     u32 _c_6 = blk_read(e.mem, 0, _at_0, _at_1 + 6);
     u32 _c_7 = blk_read(e.mem, 0, _at_0, _at_1 + 7);
-    Term _at_2 = blk_loc(e.mem, _b_0);
+    Term _at_2 = _b_0 == h6 ? q6 : blk_loc(e.mem, _b_0);
     Term _at_3 = blk_at(_b_0, U32_BIN(_j_1, *, _tku_1), 3);
     u32 _c_8 = blk_read(e.mem, 0, _at_2, _at_3 + 0);
@@ -45,5 +47,5 @@
     u32 _v_20 = 0;
     Term _o_0[6];
-    if (spin_9(e, _o_0, _tk_1, U32_BIN(_i_1, *, _tku_1), U32_BIN(_j_1, *, _tku_1), 0ull, 0ull, 0ull, 0ull, _a_0, _c_0, _c_1, _c_2, _c_3, _c_4, _c_5, _c_6, _c_7, _b_0, _c_8, _c_9, _c_10, _c_11, _c_12, _c_13, _c_14, _c_15) == 0) {
+    if (spin_9(e, _o_0, _tk_1, U32_BIN(_i_1, *, _tku_1), U32_BIN(_j_1, *, _tku_1), 0ull, 0ull, 0ull, 0ull, _a_0, _a_0 == h5 ? q5 : blk_loc(e.mem, _a_0), _c_0, _c_1, _c_2, _c_3, _c_4, _c_5, _c_6, _c_7, _b_0, _b_0 == h6 ? q6 : blk_loc(e.mem, _b_0), _c_8, _c_9, _c_10, _c_11, _c_12, _c_13, _c_14, _c_15) == 0) {
       return 0;
     }
@@ -64,5 +66,5 @@
     u32 _v_29 = 0;
     Term _o_2[3];
-    if (spin_10(e, _o_2, _rot_1, _v_9, _v_10, _v_11, _v_12, _v_13, _v_14) == 0) {
+    if (spin_10(e, _o_2, _rot_1, _v_9, _v_9 == h6 ? q6 : _v_9 == h5 ? q5 : blk_loc(e.mem, _v_9), _v_10, _v_10 == h6 ? q6 : _v_10 == h5 ? q5 : blk_loc(e.mem, _v_10), _v_11, _v_12, _v_13, _v_14) == 0) {
       return 0;
     }
--- parent/(outside any function)
+++ commit/(outside any function)
@@ -599,4 +599,5 @@
 #define ACR RLX
 #define a32_acq(p) FENCE()
+#define w64_load(p) (*(p))
 #else
 #define REL memory_order_release
@@ -604,4 +605,5 @@
 #define ACR memory_order_acq_rel
 #define a32_acq(p) ((void)a32_load_acq(p))
+#define w64_load(p) atomic_load_explicit((_Atomic u64*)(p), RLX)
 #endif
 
@@ -744,6 +746,6 @@
 
 // A redirect cell holds its target's loc over a 24-bit count, which
-// changes by atomic adds on the low half: the cell is read as two atomic
-// halves, never as one plain word.
+// changes by atomic adds on the low half, so a host never reads it as one
+// plain word.
 
 
--- parent/WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_PK_PACK_K99
+++ commit/WL_FID_0X0159E1F0F11CC1D285AC6A993D19BA8A_MAIN_PK_PACK_K99
```
1492 more lines in `c.diff`, the whole file's diff.

## Again

From a clone of this repository (bun, clang and valgrind on PATH):

```sh
make data
scripts/count.sh 6de56b973213 gemm-fork
scripts/count.sh ef66a7ccf5d0 gemm-fork
scripts/bisect.sh gemm-fork v2.0.32 v2.0.33 ir
```

The run: https://github.com/nuxyel/metalbend/actions/runs/42387765688.
