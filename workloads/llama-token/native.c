// llama-token's target: the same model (lib/mb.h's values at the same cells), the same 32 tokens, and bend-ml-llama's
// order of operations: tensor-array's dot for every product (four sums that rotate, then (a0 + a1) + (a2 + a3)),
// RMSNorm with its squares added as a balanced tree, RoPE's two halves, a softmax that subtracts the maximum and adds
// from the left, SiLU as x / (1 + exp(-x)), and Bend's math calls (exp, cos, sin, pow and sqrt in double, rounded to
// float). It keeps every vector in an array where the package keeps a list. Built with Bend's flags: clang -std=c11
// -O3.
#include "../../lib/mb.h"

enum { KV = 3, G = 3, HALF = 32, HEAD = 64, HEADS = 9, DIM = 576, KVW = 192, FFN = 1536, LAYERS = 2, VOCAB = 3072,
       POS = 32 };
#define EPS 0.00001f
#define THETA 100000.0f

typedef struct {
  float *ln1, *q, *k, *v, *o, *ln2, *gate, *up, *down;
  float *keys[KV], *vals[KV];   // the cache: a key/value head's rotated keys and its values, position p at p * HEAD
} Layer;

// a norm's gains: 1 + 0.2 * value i of the seed
static float *gains(int n, uint32_t seed) {
  float *g = mb_zeros(n);
  for (int i = 0; i < n; i++) g[i] = 1.0f + mb_val(seed, (uint32_t)i) * 0.2f;
  return g;
}

// an r x c matrix: cell i is the seed's value i times s
static float *matrix(int r, int c, uint32_t seed, float s) {
  float *w = mb_zeros((size_t)r * c);
  mb_rand_s(w, (size_t)r * c, seed, s);
  return w;
}

// tensor-array's dot of n numbers of a (sa apart) and b (sb apart)
static float dot(int n, const float *a, int sa, const float *b, int sb) {
  float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
  for (int p = 0; p < n; p++) {
    float t = a0 + a[(size_t)p * sa] * b[(size_t)p * sb];
    a0 = a1; a1 = a2; a2 = a3; a3 = t;
  }
  return (a0 + a1) + (a2 + a3);
}

// y = W · x, W r x c with one row per output
static void matvec(int r, int c, const float *w, const float *x, float *y) {
  for (int j = 0; j < r; j++) y[j] = dot(c, w + (size_t)j * c, 1, x, 1);
}

// g * (x * (1 / sqrt(mean(x²) + eps))): the squares are added in adjacent pairs, level by level (an odd last one
// moves up as it is), as tree_sum does
static void rmsnorm(const float *x, const float *g, float *y) {
  float sq[DIM];
  for (int i = 0; i < DIM; i++) sq[i] = x[i] * x[i];
  for (int n = DIM; n > 1;) {
    int m = 0;
    for (int i = 0; i + 1 < n; i += 2) sq[m++] = sq[i] + sq[i + 1];
    if (n & 1) sq[m++] = sq[n - 1];
    n = m;
  }
  float r = 1.0f / (float)sqrt((double)(sq[0] / (float)DIM + EPS));
  for (int i = 0; i < DIM; i++) y[i] = g[i] * (r * x[i]);
}

// the cosines and sines of position t, one per frequency: inv_freq[i] = 1 / theta^(2i / head)
static void rot_at(int t, float *cs, float *sn) {
  for (int i = 0; i < HALF; i++) {
    float f = 1.0f / (float)pow((double)THETA, (double)((float)(2 * i) / (float)HEAD));
    float a = (float)t * f;
    cs[i] = (float)cos((double)a);
    sn[i] = (float)sin((double)a);
  }
}

// RoPE on one head: first half lo * cos + (-hi) * sin, second half hi * cos + lo * sin
static void rope(const float *h, const float *cs, const float *sn, float *out) {
  for (int i = 0; i < HALF; i++) {
    float lo = h[i], hi = h[HALF + i];
    out[i] = lo * cs[i] + (-hi) * sn[i];
    out[HALF + i] = hi * cs[i] + lo * sn[i];
  }
}

// one query head at position t over its key/value head's cache: softmax(q · K / sqrt(head)) · V, over the n keys of
// positions 0..t
static void head_att(int t, const float *q, const float *keys, const float *vals, float *out) {
  int n = t + 1;
  float s[POS + 1] = {0}, scale = 1.0f / (float)sqrt((double)(float)HEAD);
  for (int p = 0; p < n; p++) s[p] = scale * dot(HEAD, q, 1, keys + (size_t)p * HEAD, 1);
  float mx = s[0];
  for (int p = 1; p < n; p++) mx = mx < s[p] ? s[p] : mx;
  float sum = 0.0f;
  for (int p = 0; p < n; p++) { s[p] = (float)exp((double)(s[p] - mx)); sum = sum + s[p]; }
  for (int p = 0; p < n; p++) s[p] = s[p] / sum;
  for (int c = 0; c < HEAD; c++) out[c] = dot(n, s, 1, vals + c, HEAD);
}

// the layer at position t: x in, y out, its cache grown by the position
static void block(Layer *l, int t, const float *cs, const float *sn, const float *x, float *y) {
  static float n1[DIM], q[DIM], k[KVW], v[KVW], qr[DIM], at[DIM], a[DIM], x1[DIM], n2[DIM], g[FFN], u[FFN], m[FFN],
    dn[DIM];
  rmsnorm(x, l->ln1, n1);
  matvec(DIM, DIM, l->q, n1, q);
  matvec(KVW, DIM, l->k, n1, k);
  matvec(KVW, DIM, l->v, n1, v);
  for (int h = 0; h < HEADS; h++) rope(q + h * HEAD, cs, sn, qr + h * HEAD);
  for (int j = 0; j < KV; j++) {
    rope(k + j * HEAD, cs, sn, l->keys[j] + (size_t)t * HEAD);
    memcpy(l->vals[j] + (size_t)t * HEAD, v + j * HEAD, HEAD * sizeof(float));
  }
  // query heads j * G .. j * G + G - 1 read key/value head j
  for (int h = 0; h < HEADS; h++) head_att(t, qr + h * HEAD, l->keys[h / G], l->vals[h / G], at + h * HEAD);
  matvec(DIM, DIM, l->o, at, a);
  for (int i = 0; i < DIM; i++) x1[i] = x[i] + a[i];
  rmsnorm(x1, l->ln2, n2);
  matvec(FFN, DIM, l->gate, n2, g);
  matvec(FFN, DIM, l->up, n2, u);
  for (int i = 0; i < FFN; i++) m[i] = (g[i] / (1.0f + (float)exp((double)(-g[i])))) * u[i];
  matvec(DIM, FFN, l->down, m, dn);
  for (int i = 0; i < DIM; i++) y[i] = x1[i] + dn[i];
}

int main(void) {
  float *emb = matrix(VOCAB, DIM, 1, 1.0f), *lnf = gains(DIM, 2);
  Layer ls[LAYERS];
  for (int i = 0; i < LAYERS; i++) {
    uint32_t sd = 16u + 16u * (uint32_t)i;
    ls[i] = (Layer){gains(DIM, sd), matrix(DIM, DIM, sd + 1, 0.1443f), matrix(KVW, DIM, sd + 2, 0.1443f),
                    matrix(KVW, DIM, sd + 3, 0.1443f), matrix(DIM, DIM, sd + 4, 0.1443f), gains(DIM, sd + 5),
                    matrix(FFN, DIM, sd + 6, 0.1443f), matrix(FFN, DIM, sd + 7, 0.1443f),
                    matrix(DIM, FFN, sd + 8, 0.0884f), {0}, {0}};
    for (int j = 0; j < KV; j++) { ls[i].keys[j] = mb_zeros(POS * HEAD); ls[i].vals[j] = mb_zeros(POS * HEAD); }
  }
  float cs[HALF], sn[HALF], x[DIM], y[DIM], nf[DIM], *lg = mb_zeros(VOCAB);
  for (int t = 0; t < POS; t++) {
    int tok = (t * 911 + 7) % VOCAB;
    memcpy(x, emb + (size_t)tok * DIM, sizeof x);
    rot_at(t, cs, sn);
    for (int i = 0; i < LAYERS; i++) { block(&ls[i], t, cs, sn, x, y); memcpy(x, y, sizeof x); }
    rmsnorm(x, lnf, nf);
    matvec(VOCAB, DIM, emb, nf, lg);
    mb_show_hash(lg, VOCAB);
  }
  return 0;
}
