// gemm-tile8's target: the same three products, the same 8 repetitions, the same order of additions as tensor-array's
// Tile8 loop: product p of a dot goes to partial sum p mod 4, the four sums combined as (s0 + s1) + (s2 + s3) (k is a
// multiple of 4 in all three shapes), and each dot added once into C. Built with Bend's flags: clang -std=c11 -O3.
#include "../../lib/mb.h"

// C(n x m) += A · B, where A(i, p) = a[i * ai + p * ap] and B(p, j) = b[p * bp + j * bj]. As Tile8 does, both operands
// are first packed so that row i of A and column j of B are contiguous; then each cell is one dot over two lines.
static void gemm_acc(int n, int m, int k, const float *a, int ai, int ap, const float *b, int bp, int bj, float *c) {
  float *pa = malloc((size_t)n * k * sizeof(float)), *pb = malloc((size_t)m * k * sizeof(float));
  for (int i = 0; i < n; i++)
    for (int p = 0; p < k; p++) pa[(size_t)i * k + p] = a[i * ai + p * ap];
  for (int j = 0; j < m; j++)
    for (int p = 0; p < k; p++) pb[(size_t)j * k + p] = b[p * bp + j * bj];
  for (int i = 0; i < n; i++) {
    const float *x = pa + (size_t)i * k;
    for (int j = 0; j < m; j++) {
      const float *y = pb + (size_t)j * k;
      float s0 = 0, s1 = 0, s2 = 0, s3 = 0;
      for (int p = 0; p < k; p += 4) {
        s0 = s0 + x[p + 0] * y[p + 0];
        s1 = s1 + x[p + 1] * y[p + 1];
        s2 = s2 + x[p + 2] * y[p + 2];
        s3 = s3 + x[p + 3] * y[p + 3];
      }
      c[i * m + j] = c[i * m + j] + ((s0 + s1) + (s2 + s3));
    }
  }
  free(pa); free(pb);
}

int main(void) {
  enum { REPS = 8 };
  // nt: C(256 x 1536) += A(256 x 576) · B(1536 x 576)ᵀ
  float *a = mb_zeros(256 * 576), *b = mb_zeros(1536 * 576), *c = mb_zeros(256 * 1536);
  mb_rand(a, 256 * 576, 1); mb_rand(b, 1536 * 576, 2);
  for (int r = 0; r < REPS; r++) gemm_acc(256, 1536, 576, a, 576, 1, b, 1, 576, c);
  mb_show_hash(c, 256 * 1536);
  free(a); free(b); free(c);
  // tn: C(1536 x 576) += A(256 x 1536)ᵀ · B(256 x 576)
  a = mb_zeros(256 * 1536); b = mb_zeros(256 * 576); c = mb_zeros(1536 * 576);
  mb_rand(a, 256 * 1536, 3); mb_rand(b, 256 * 576, 4);
  for (int r = 0; r < REPS; r++) gemm_acc(1536, 576, 256, a, 1, 1536, b, 576, 1, c);
  mb_show_hash(c, 1536 * 576);
  free(a); free(b); free(c);
  // nn: C(256 x 576) += A(256 x 1536) · B(1536 x 576)
  a = mb_zeros(256 * 1536); b = mb_zeros(1536 * 576); c = mb_zeros(256 * 576);
  mb_rand(a, 256 * 1536, 5); mb_rand(b, 1536 * 576, 6);
  for (int r = 0; r < REPS; r++) gemm_acc(256, 576, 1536, a, 1536, 1, b, 576, 1, c);
  mb_show_hash(c, 256 * 576);
  free(a); free(b); free(c);
  return 0;
}
