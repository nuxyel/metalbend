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

// the final state as the Bend workloads print it: one FNV-1a over the weights of the k matrices in Layer.store's
// order, then their first moments, then their second moments (lib/mb.bend's hash of that one array); the gradients
// are zero after a step
static void bt_show_state(bt_param *const *ps, int k) {
  uint32_t h = MB_FNV_START;
  for (int i = 0; i < k; i++) h = mb_fnv(h, ps[i]->w, ps[i]->n);
  for (int i = 0; i < k; i++) h = mb_fnv(h, ps[i]->m, ps[i]->n);
  for (int i = 0; i < k; i++) h = mb_fnv(h, ps[i]->v, ps[i]->n);
  printf("%u\n", h);
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

// ---- products: tensor-array's Tile8 cells (0.1.14.0; tensor-fork gives the same bits at every depth) ----
// C(n x m) = A · B, or C + A · B when ac, with A(i, p) = a[i * ai + p * ap] and B(p, j) = b[p * bp + j * bj]: both
// packed into contiguous lines first, product p of a dot to partial sum p mod 4, combined as (s0 + s1) + (s2 + s3)
// (every k here is a multiple of 8, so no padding and no rotation), each dot written into C or added once to it.
static void bt_gemm(int ac, int n, int m, int k, const float *a, int ai, int ap, const float *b, int bp, int bj, float *c) {
  if (k % 8 != 0) { fprintf(stderr, "bt_gemm: k = %d is not a multiple of 8\n", k); exit(1); }
  float *pa = malloc((size_t)n * k * sizeof(float)), *pb = malloc((size_t)m * k * sizeof(float));
  for (int i = 0; i < n; i++)
    for (int p = 0; p < k; p++) pa[(size_t)i * k + p] = a[(size_t)i * ai + (size_t)p * ap];
  for (int j = 0; j < m; j++)
    for (int p = 0; p < k; p++) pb[(size_t)j * k + p] = b[(size_t)p * bp + (size_t)j * bj];
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
      float d = (s0 + s1) + (s2 + s3);
      c[(size_t)i * m + j] = ac ? c[(size_t)i * m + j] + d : d;
    }
  }
  free(pa); free(pb);
}

// tensor-array's matmul_precise, C = A · B (A n x k, B k x m, row-major): k in blocks of 1024, the first block's
// product written into C, each next one's added to it; k <= 1024 is the plain product
static void bt_matmul_precise(int n, int k, int m, const float *a, const float *b, float *c) {
  for (int p0 = 0; p0 < k; p0 += 1024) {
    int w = k - p0 < 1024 ? k - p0 : 1024;
    bt_gemm(p0 > 0, n, m, w, a + p0, k, 1, b + (size_t)p0 * m, m, 1, c);
  }
}

// ---- LinearNB: y = x · Wᵀ (W o x i); backward dx = dy · W (precise), then dW += dyᵀ · x ----

static void bt_lin_fwd(int n, int i, int o, const float *w, const float *x, float *y) {
  bt_gemm(0, n, o, i, x, i, 1, w, 1, i, y);
}

static void bt_lin_bwd(int n, int i, int o, const float *w, const float *x, const float *dy, float *dx, float *gw) {
  bt_matmul_precise(n, o, i, dy, w, dx);
  bt_gemm(1, o, i, n, dy, 1, o, x, i, 1, gw);
}

// ---- RoPE, rotate-half: row r is position r mod t, each row h heads of 2 half numbers; the pair (c, c + half) of a
// head rotated by pos * inv[c], inv[c] = 1 / base^(2c / (2 half)); the backward pass by the opposite angle ----

typedef struct { int t, half; float *cs, *sn; } bt_rope_tab;

static bt_rope_tab bt_rope_new(int t, int half, float base) {
  bt_rope_tab r = {t, half, mb_zeros((size_t)t * half), mb_zeros((size_t)t * half)};
  for (int e = 0; e < t * half; e++) {
    uint32_t c = (uint32_t)(e % half), h2 = (uint32_t)(half + half);
    float inv = 1.0f / (float)pow((double)base, (double)((float)(c + c) / (float)h2));
    float ang = inv * (float)(uint32_t)(e / half);
    r.cs[e] = (float)cos((double)ang); r.sn[e] = (float)sin((double)ang);
  }
  return r;
}

static void bt_rope(int fwd, const bt_rope_tab *tb, int n, int w, int h, float *x) {
  const int half = tb->half, hh = h * half;
  for (int e = 0; e < n * hh; e++) {
    int r = e / hh, c = (e % hh) % half;
    size_t i1 = (size_t)r * w + (size_t)((e % hh) / half) * (half + half) + c, i2 = i1 + half;
    int kk = (r % tb->t) * half + c;
    float a = x[i1], b = x[i2], cs = tb->cs[kk], z = tb->sn[kk];
    if (fwd) { x[i1] = a * cs + (-b) * z; x[i2] = b * cs + a * z; }
    else { x[i1] = a * cs + b * z; x[i2] = b * cs + -(a * z); }
  }
}

// ---- causal attention, grouped-query: q n x (kv g hd), k and v n x (kv hd), rows b sequences of t positions; query
// head h reads key/value head h / g. Every sum runs left to right from +0, over all t positions where BendTorch's do
// (the zeros of P and G past the diagonal included) ----

typedef struct { int b, t, kv, g, hd; float sc; } bt_attn;

// row i of a head's P (t x t, rows from p): the scaled scores against keys 0..i, softmaxed in place over those i + 1
static void bt_prow(const bt_attn *A, int i, const float *q, int qs, const float *k, int ks, float *p) {
  float *row = p + (size_t)i * A->t;
  for (int l = 0; l <= i; l++) {
    float s = 0.0f;
    for (int d = 0; d < A->hd; d++) s = s + q[(size_t)i * qs + d] * k[(size_t)l * ks + d];
    row[l] = s * A->sc;
  }
  float m = row[0];
  for (int l = 1; l <= i; l++) m = m < row[l] ? row[l] : m;
  float s = 0.0f;
  for (int l = 0; l <= i; l++) { row[l] = (float)exp((double)(row[l] - m)); s = s + row[l]; }
  for (int l = 0; l <= i; l++) row[l] = row[l] / s;
}

// P of one head; q, k point at the head's first column of row 0 of the sequence
static void bt_probs(const bt_attn *A, const float *q, int qs, const float *k, int ks, float *p) {
  memset(p, 0, (size_t)A->t * A->t * sizeof(float));
  for (int i = 0; i < A->t; i++) bt_prow(A, i, q, qs, k, ks, p);
}

// o = attention(q, k, v); p is a t x t scratch
static void bt_attn_fwd(const bt_attn *A, const float *q, const float *k, const float *v, float *o, float *p) {
  const int t = A->t, hd = A->hd, w = A->kv * A->g * hd, kvw = A->kv * hd;
  for (int bi = 0; bi < A->b; bi++)
    for (int h = 0; h < A->kv * A->g; h++) {
      size_t r0 = (size_t)bi * t;
      const float *qh = q + r0 * w + (size_t)h * hd, *kh = k + r0 * kvw + (size_t)(h / A->g) * hd;
      const float *vh = v + r0 * kvw + (size_t)(h / A->g) * hd;
      bt_probs(A, qh, w, kh, kvw, p);
      for (int i = 0; i < t; i++)
        for (int d = 0; d < hd; d++) {
          float s = 0.0f;
          for (int l = 0; l < t; l++) s = s + p[(size_t)i * t + l] * vh[(size_t)l * kvw + d];
          o[(r0 + i) * w + (size_t)h * hd + d] = s;
        }
    }
}

// dq, dk, dv from do (dd): per sequence and key/value head, its g query heads in order: P again, G = (P * (dP - s))
// * scale with s = sum(dP * P) over the row's i + 1 positions, dQ = G · K, then dK += Gᵀ · Q and dV += Pᵀ · dO into
// the group's sums (from +0); p, gm are t x t and ka, va t x hd scratch
static void bt_attn_bwd(const bt_attn *A, const float *q, const float *k, const float *v, const float *dd, float *dq,
                        float *dk, float *dv, float *p, float *gm, float *ka, float *va) {
  const int t = A->t, hd = A->hd, w = A->kv * A->g * hd, kvw = A->kv * hd;
  for (int bi = 0; bi < A->b; bi++)
    for (int j = 0; j < A->kv; j++) {
      size_t r0 = (size_t)bi * t;
      const float *kh = k + r0 * kvw + (size_t)j * hd, *vh = v + r0 * kvw + (size_t)j * hd;
      memset(ka, 0, (size_t)t * hd * sizeof(float));
      memset(va, 0, (size_t)t * hd * sizeof(float));
      for (int h = j * A->g; h < (j + 1) * A->g; h++) {
        const float *qh = q + r0 * w + (size_t)h * hd, *dh = dd + r0 * w + (size_t)h * hd;
        bt_probs(A, qh, w, kh, kvw, p);
        memset(gm, 0, (size_t)t * t * sizeof(float));
        for (int i = 0; i < t; i++) {
          float *g = gm + (size_t)i * t;
          const float *pr = p + (size_t)i * t;
          for (int l = 0; l <= i; l++) {
            float s = 0.0f;
            for (int d = 0; d < hd; d++) s = s + dh[(size_t)i * w + d] * vh[(size_t)l * kvw + d];
            g[l] = s;
          }
          float s = 0.0f;
          for (int l = 0; l <= i; l++) s = s + g[l] * pr[l];
          for (int l = 0; l <= i; l++) g[l] = (pr[l] * (g[l] - s)) * A->sc;
        }
        for (int i = 0; i < t; i++)
          for (int d = 0; d < hd; d++) {
            float s = 0.0f;
            for (int l = 0; l < t; l++) s = s + gm[(size_t)i * t + l] * kh[(size_t)l * kvw + d];
            dq[(r0 + i) * w + (size_t)h * hd + d] = s;
          }
        for (int l = 0; l < t; l++)
          for (int d = 0; d < hd; d++) {
            float s = 0.0f;
            for (int i = 0; i < t; i++) s = s + gm[(size_t)i * t + l] * qh[(size_t)i * w + d];
            ka[(size_t)l * hd + d] = ka[(size_t)l * hd + d] + s;
          }
        for (int l = 0; l < t; l++)
          for (int d = 0; d < hd; d++) {
            float s = 0.0f;
            for (int i = 0; i < t; i++) s = s + p[(size_t)i * t + l] * dh[(size_t)i * w + d];
            va[(size_t)l * hd + d] = va[(size_t)l * hd + d] + s;
          }
      }
      for (int l = 0; l < t; l++)
        for (int d = 0; d < hd; d++) {
          dk[(r0 + l) * kvw + (size_t)j * hd + d] = ka[(size_t)l * hd + d];
          dv[(r0 + l) * kvw + (size_t)j * hd + d] = va[(size_t)l * hd + d];
        }
    }
}

// a = a + b, element by element (Mat.sum2: a Fork's two input gradients, a Residual's sum)
static void bt_add(size_t n, float *a, const float *b) {
  for (size_t i = 0; i < n; i++) a[i] = a[i] + b[i];
}

// ---- SiLU as PyTorch's CPU kernel computes it: x / (1 + exp(-x)); its gradient dy s (1 + x (1 - s)), s = sigmoid(x) ----

static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)); }

static inline float bt_silu_d(float dy, float x) {
  float s = 1.0f / (1.0f + (float)exp((double)-x));
  return (dy * s) * (1.0f + x * (1.0f - s));
}
