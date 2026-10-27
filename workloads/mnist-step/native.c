// mnist-step's target: bend-ml's MNIST step (784-128-10, batch 100, SGD at 0.1) on the same synthetic batches, in
// tensor-array's order of operations. Every product is tensor-array's dot (dotr: each product to the first of four
// rotating sums, then (a0 + a1) + (a2 + a3); Tile8 gives the same bits, and dot4 below is that form, on packed lines); column sums are that dot against ones; the
// bias is added as c + b; relu is (v < 0 ? 0 : v); the cross entropy is softmax-ce's. Bend's flags: -std=c11 -O3.
#include "../../lib/mb.h"

// tensor-array's dotr over k products x[p * sx] * y[p * sy]
static float dotr(int k, const float *x, int sx, const float *y, int sy) {
  float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
  for (int p = 0; p < k; p++) {
    float t = a0 + x[p * sx] * y[p * sy];
    a0 = a1; a1 = a2; a2 = a3; a3 = t;
  }
  return (a0 + a1) + (a2 + a3);
}

// the same dot written as Tile8 does: product p to sum p mod 4, the sums combined as dotr leaves them after k steps
static float dot4(int k, const float *x, const float *y) {
  float s0 = 0, s1 = 0, s2 = 0, s3 = 0;
  int p = 0;
  for (; p + 4 <= k; p += 4) {
    s0 = s0 + x[p] * y[p]; s1 = s1 + x[p + 1] * y[p + 1]; s2 = s2 + x[p + 2] * y[p + 2]; s3 = s3 + x[p + 3] * y[p + 3];
  }
  if (p < k) s0 = s0 + x[p] * y[p];
  if (p + 1 < k) s1 = s1 + x[p + 1] * y[p + 1];
  if (p + 2 < k) s2 = s2 + x[p + 2] * y[p + 2];
  switch (k & 3) {
    case 0: return (s0 + s1) + (s2 + s3);
    case 1: return (s1 + s2) + (s3 + s0);
    case 2: return (s2 + s3) + (s0 + s1);
    default: return (s3 + s0) + (s1 + s2);
  }
}

// C(n x m) = A · B, A(i, p) = a[i * ai + p * ap], B(p, j) = b[p * bp + j * bj]; both packed into lines first
static void mm(int n, int m, int k, const float *a, int ai, int ap, const float *b, int bp, int bj, float *c) {
  float *pa = malloc((size_t)n * k * sizeof(float)), *pb = malloc((size_t)m * k * sizeof(float));
  for (int i = 0; i < n; i++) for (int p = 0; p < k; p++) pa[i * k + p] = a[i * ai + p * ap];
  for (int j = 0; j < m; j++) for (int p = 0; p < k; p++) pb[j * k + p] = b[p * bp + j * bj];
  for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++) c[i * m + j] = dot4(k, pa + i * k, pb + j * k);
  free(pa); free(pb);
}

static void col_sums(int n, int m, const float *a, float *s) {
  static float ones[128];
  for (int i = 0; i < n; i++) ones[i] = 1.0f;
  for (int j = 0; j < m; j++) s[j] = dotr(n, ones, 1, a + j, m);
}

static uint32_t label(uint32_t seed, uint32_t i) { return (((i + seed) * 2654435761u) >> 7) % 10u; }

enum { B = 100, I = 784, H = 128, O = 10 };

int main(void) {
  float *w1 = mb_zeros(I * H), *b1 = mb_zeros(H), *w2 = mb_zeros(H * O), *b2 = mb_zeros(O);
  float *x = mb_zeros(B * I), *z1 = mb_zeros(B * H), *z2 = mb_zeros(B * O), *dw2 = mb_zeros(H * O), *dh = mb_zeros(B * H);
  float *db2 = mb_zeros(O), *dw1 = mb_zeros(I * H), *db1 = mb_zeros(H), e[O];
  mb_rand_s(w1, I * H, 1, 0.124f);
  mb_rand_s(w2, H * O, 2, 0.306f);
  const float lr = 0.1f, nf = (float)B;
  float acc = 0.0f, l = 0.0f;
  for (uint32_t bt = 0; bt < 200; bt++) {
    acc = acc + l;
    mb_rand(x, B * I, 1000 + bt);
    // forward: z1 = x · w1 + b1, h = relu(z1) (in z1), z2 = h · w2 + b2
    mm(B, H, I, x, I, 1, w1, H, 1, z1);
    for (int i = 0; i < B; i++) for (int j = 0; j < H; j++) z1[i * H + j] = z1[i * H + j] + b1[j];
    for (int t = 0; t < B * H; t++) z1[t] = z1[t] < 0.0f ? 0.0f : z1[t];
    mm(B, O, H, z1, H, 1, w2, O, 1, z2);
    for (int i = 0; i < B; i++) for (int j = 0; j < O; j++) z2[i * O + j] = z2[i * O + j] + b2[j];
    // softmax cross entropy, the gradient written over z2; row i's label is that of index 99 - i
    float loss = 0.0f;
    for (int i = 0; i < B; i++) {
      uint32_t y = label(bt * 100, (B - 1) - (uint32_t)i);
      float *row = z2 + i * O, m = row[0], s = 0.0f;
      for (int j = 1; j < O; j++) m = m < row[j] ? row[j] : m;
      for (int j = 0; j < O; j++) e[j] = (float)exp((double)(row[j] - m));
      for (int j = 0; j < O; j++) s = s + e[j];
      for (int j = 0; j < O; j++) e[j] = e[j] / s;
      float py = e[y], lo = 0.000000000001f;
      loss = loss - (float)log((double)(py < lo ? lo : py));
      for (int j = 0; j < O; j++) row[j] = (e[j] - (j == (int)y ? 1.0f : 0.0f)) / nf;
    }
    l = loss / nf;
    // backward: dw2 = hᵀ · g2, dh = g2 · w2ᵀ, db2, dz1 = dh * (h > 0) (in dh), dw1 = xᵀ · dz1, db1
    mm(H, O, B, z1, 1, H, z2, O, 1, dw2);
    mm(B, H, O, z2, O, 1, w2, 1, O, dh);
    col_sums(B, O, z2, db2);
    for (int t = 0; t < B * H; t++) dh[t] = dh[t] * (z1[t] > 0.0f ? 1.0f : 0.0f);
    mm(I, H, B, x, 1, I, dh, H, 1, dw1);
    col_sums(B, H, dh, db1);
    for (int t = 0; t < I * H; t++) w1[t] = w1[t] - lr * dw1[t];
    for (int t = 0; t < H; t++) b1[t] = b1[t] - lr * db1[t];
    for (int t = 0; t < H * O; t++) w2[t] = w2[t] - lr * dw2[t];
    for (int t = 0; t < O; t++) b2[t] = b2[t] - lr * db2[t];
  }
  acc = acc + l;
  printf("%u\n", f2u(acc));
  mb_show_hash(w1, I * H); mb_show_hash(b1, H); mb_show_hash(w2, H * O); mb_show_hash(b2, O);
  return 0;
}
