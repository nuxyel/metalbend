// BendTorch's layers in C, for the C targets of the block workloads (rmsnorm-step, attention-step, block-step): the
// same inputs (demo/smol_block.bend's hash of each index), the same loops in the same order of operations as
// bendtorch@1.1.1.0 and bendtorch-fast@1.1.1.0, so the same bits. exp, sqrt and pow go through libm's double versions
// rounded to F32, as Bend emits them; Bend's C has `fp contract(off)`, and so has this file.
#pragma clang fp contract(off)
#include "mb.h"

// ---- inputs: (h mod 65536 - 32768) * sc, h a hash of the index i under the seed s (smol_block.bend's gen) ----

static inline uint32_t bt_hsh(uint32_t i, uint32_t s) {
  uint32_t x0 = i * 2654435761u + s * 40503u;
  uint32_t x1 = x0 ^ (x0 >> 15);
  uint32_t x2 = x1 * 2246822519u;
  return x2 ^ (x2 >> 13);
}

static inline void bt_gen(float *a, size_t n, uint32_t s, float sc) {
  for (size_t i = 0; i < n; i++) a[i] = ((float)(bt_hsh((uint32_t)i, s) % 65536u) - 32768.0f) * sc;
}

// weights in about +-1/64 (2^-21), inputs and targets in about +-1 (2^-15)
#define BT_W_SCALE 0.000000476837158203125f
#define BT_X_SCALE 0.000030517578125f

// ---- AdamW (CAdamW{0.001, 0.9, 0.999, 1e-8, 0.01, 0.1, 0.001}) ----

typedef struct { float lr, c1, b2, c2, eps, wd, step, bc2; } bt_opt;

// Train.step's q1 = p1 + c1 (1 - p1), q2 = p2 + c2 (1 - p2) from 0, then Opt.at: step = lr / q1, bc2 = sqrt(q2)
typedef struct { float p1, p2; } bt_train;

static inline bt_opt bt_opt_next(bt_train *t) {
  const float lr = 0.001f, c1 = 0.1f, b2 = 0.999f, c2 = 0.001f, eps = 0.00000001f, wd = 0.01f;
  float q1 = t->p1 + c1 * (1.0f - t->p1), q2 = t->p2 + c2 * (1.0f - t->p2);
  t->p1 = q1; t->p2 = q2;
  return (bt_opt){lr, c1, b2, c2, eps, wd, lr / q1, (float)sqrt((double)q2)};
}

// adam_l over one matrix: w, its gradient g (zeroed) and its moments m, v
static void bt_adam(const bt_opt *o, size_t n, float *w, float *g, float *m, float *v) {
  for (size_t i = 0; i < n; i++) {
    float gg = g[i];
    float nm = m[i] + o->c1 * (gg - m[i]);
    float nv = v[i] * o->b2 + (o->c2 * gg) * gg;
    float dw = w[i] * (1.0f - o->lr * o->wd);
    w[i] = dw + (-o->step * nm) / ((float)sqrt((double)nv) / o->bc2 + o->eps);
    g[i] = 0.0f; m[i] = nm; v[i] = nv;
  }
}

// a parameter matrix with its gradient and moments
typedef struct { size_t n; float *w, *g, *m, *v; } bt_param;

static bt_param bt_param_new(size_t n) {
  return (bt_param){n, mb_zeros(n), mb_zeros(n), mb_zeros(n), mb_zeros(n)};
}

// ---- tree_sum: a[i] = a[2i] + a[2i + 1], an odd last one carried, until one number is left (destroys a) ----

static float bt_tree_sum(float *a, uint32_t m) {
  while (m > 1) {
    uint32_t h = m / 2;
    for (uint32_t i = 0; i < h; i++) a[i] = a[2 * i] + a[2 * i + 1];
    if (m % 2 == 1) a[h] = a[m - 1];
    m = (m + 1) / 2;
  }
  return a[0];
}

// ---- MSE: d = y - t, dy = d * (2 / (n c)) written over y, the loss the tree sum of d * d over n c ----

static float bt_mse(size_t n, float *y, const float *t, float *q) {
  const float nc = (float)n, kk = 2.0f / nc;
  for (size_t i = 0; i < n; i++) {
    float d = y[i] - t[i];
    q[i] = d * d;
    y[i] = d * kk;
  }
  return bt_tree_sum(q, (uint32_t)n) / nc;
}

// ---- RMSNorm over n rows of d, gain g: y = g * (x * r), r = 1 / sqrt(sum(x^2) / d + eps), each sum from +0 in order ----

static inline float bt_rms_r(const float *x, int d, float eps) {
  float s = 0.0f;
  for (int j = 0; j < d; j++) s = s + x[j] * x[j];
  return 1.0f / (float)sqrt((double)(s / (float)d + eps));
}

static void bt_rms_fwd(int n, int d, float eps, const float *g, const float *x, float *y) {
  for (int i = 0; i < n; i++) {
    const float *xr = x + (size_t)i * d;
    float r = bt_rms_r(xr, d, eps);
    for (int j = 0; j < d; j++) y[(size_t)i * d + j] = g[j] * (xr[j] * r);
  }
}

// dx = ((dy g) - (x r) m) r with m = sum((dy g)(x r)) / d; dg (zeroed, d numbers) += dy (x r) row after row, then
// added into the gradient gacc as gacc + dg
static void bt_rms_bwd(int n, int d, float eps, const float *g, const float *x, const float *dy, float *dx, float *dg,
                       float *gacc) {
  memset(dg, 0, (size_t)d * sizeof(float));
  for (int i = 0; i < n; i++) {
    const float *xr = x + (size_t)i * d, *dr = dy + (size_t)i * d;
    float r = bt_rms_r(xr, d, eps), s = 0.0f;
    for (int j = 0; j < d; j++) s = s + (dr[j] * g[j]) * (xr[j] * r);
    float m = s / (float)d;
    for (int j = 0; j < d; j++) {
      float xh = xr[j] * r;
      dx[(size_t)i * d + j] = ((dr[j] * g[j]) - xh * m) * r;
      dg[j] = dg[j] + dr[j] * xh;
    }
  }
  for (int j = 0; j < d; j++) gacc[j] = gacc[j] + dg[j];
}
