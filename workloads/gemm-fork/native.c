// gemm-fork's target: gemm-tile8's products and cells, in tensor-fork's blocks. At par 3 each product splits into 8
// blocks (tensor-array's split_depth), halved at each node as cpar and rpar halve them: by rows when C has at least as
// many rows as columns (tn, whose blocks of rows run in gemm-tile8's own order), by columns otherwise (nt and nn). A block
// of columns runs every row of C over its own columns only, so the block's packed lines of B (1/8 of them, 442 KB here)
// stay in the cache while A's rows go by, where gemm-tile8's order streams all of B (3.5 MB) once per row of C. Every cell
// is the same dot as gemm-tile8's, added once into C, so the bits are the same at every depth. Built with Bend's flags:
// clang -std=c11 -O3.
#include "../../lib/mb.h"

// cell (i, j) of C: product p of the dot goes to sum p mod 4, combined as (s0 + s1) + (s2 + s3) (k is a multiple of 4)
static inline float cell(int k, const float *x, const float *y) {
  float s0 = 0, s1 = 0, s2 = 0, s3 = 0;
  for (int p = 0; p < k; p += 4) {
    s0 = s0 + x[p + 0] * y[p + 0];
    s1 = s1 + x[p + 1] * y[p + 1];
    s2 = s2 + x[p + 2] * y[p + 2];
    s3 = s3 + x[p + 3] * y[p + 3];
  }
  return (s0 + s1) + (s2 + s3);
}

// rows i0 .. i0+cnt-1 of C, every column (rblock)
static void rows(int i0, int cnt, int m, int k, const float *pa, const float *pb, float *c) {
  for (int i = i0; i < i0 + cnt; i++)
    for (int j = 0; j < m; j++) c[i * m + j] = c[i * m + j] + cell(k, pa + (size_t)i * k, pb + (size_t)j * k);
}

// columns j0 .. j0+cnt-1 of C, every row (cbrows)
static void cols(int j0, int cnt, int n, int m, int k, const float *pa, const float *pb, float *c) {
  for (int i = 0; i < n; i++)
    for (int j = j0; j < j0 + cnt; j++) c[i * m + j] = c[i * m + j] + cell(k, pa + (size_t)i * k, pb + (size_t)j * k);
}

// 2^d blocks of 0 .. cnt-1 from s, the left half cnt / 2, as rpar and cpar split
static void tree(int byrows, int d, int s, int cnt, int n, int m, int k, const float *pa, const float *pb, float *c) {
  if (d == 0) {
    if (byrows) rows(s, cnt, m, k, pa, pb, c);
    else cols(s, cnt, n, m, k, pa, pb, c);
    return;
  }
  tree(byrows, d - 1, s, cnt / 2, n, m, k, pa, pb, c);
  tree(byrows, d - 1, s + cnt / 2, cnt - cnt / 2, n, m, k, pa, pb, c);
}

// C(n x m) += A · B in 2^d blocks, where A(i, p) = a[i * ai + p * ap] and B(p, j) = b[p * bp + j * bj]; both operands are
// packed first so that row i of A and column j of B are contiguous, as tensor-fork's pk_par packs them
static void gemm_acc(int d, int n, int m, int k, const float *a, int ai, int ap, const float *b, int bp, int bj, float *c) {
  float *pa = malloc((size_t)n * k * sizeof(float)), *pb = malloc((size_t)m * k * sizeof(float));
  for (int i = 0; i < n; i++)
    for (int p = 0; p < k; p++) pa[(size_t)i * k + p] = a[i * ai + p * ap];
  for (int j = 0; j < m; j++)
    for (int p = 0; p < k; p++) pb[(size_t)j * k + p] = b[p * bp + j * bj];
  int byrows = m <= n;
  tree(byrows, d, 0, byrows ? n : m, n, m, k, pa, pb, c);
  free(pa); free(pb);
}

int main(void) {
  enum { REPS = 8, D = 3 };
  // nt: C(256 x 1536) += A(256 x 576) · B(1536 x 576)ᵀ, 8 blocks of 192 columns
  float *a = mb_zeros(256 * 576), *b = mb_zeros(1536 * 576), *c = mb_zeros(256 * 1536);
  mb_rand(a, 256 * 576, 1); mb_rand(b, 1536 * 576, 2);
  for (int r = 0; r < REPS; r++) gemm_acc(D, 256, 1536, 576, a, 576, 1, b, 1, 576, c);
  mb_show_hash(c, 256 * 1536);
  free(a); free(b); free(c);
  // tn: C(1536 x 576) += A(256 x 1536)ᵀ · B(256 x 576), 8 blocks of 192 rows
  a = mb_zeros(256 * 1536); b = mb_zeros(256 * 576); c = mb_zeros(1536 * 576);
  mb_rand(a, 256 * 1536, 3); mb_rand(b, 256 * 576, 4);
  for (int r = 0; r < REPS; r++) gemm_acc(D, 1536, 576, 256, a, 1, 1536, b, 576, 1, c);
  mb_show_hash(c, 1536 * 576);
  free(a); free(b); free(c);
  // nn: C(256 x 576) += A(256 x 1536) · B(1536 x 576), 8 blocks of 72 columns
  a = mb_zeros(256 * 1536); b = mb_zeros(1536 * 576); c = mb_zeros(256 * 576);
  mb_rand(a, 256 * 1536, 5); mb_rand(b, 1536 * 576, 6);
  for (int r = 0; r < REPS; r++) gemm_acc(D, 256, 576, 1536, a, 1536, 1, b, 576, 1, c);
  mb_show_hash(c, 256 * 576);
  free(a); free(b); free(c);
  return 0;
}
