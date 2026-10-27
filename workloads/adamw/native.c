// adamw's target: BendTorch's adam_l in the same order of operations (PyTorch's): m += c1 * (g - m);
// v = v * b2 + (c2 * g) * g; w = w * (1 - lr * wd) + (-step * m) / (sqrt(v) / bc2 + eps), with step = lr / (1 - b1^t)
// and bc2 = sqrt(1 - b2^t); sqrt through libm's double sqrt rounded to F32, as Bend emits it. Bend's flags: -std=c11 -O3.
#include "../../lib/mb.h"

enum { N = 28311552 };

int main(void) {
  const float lr = 0.001f, b1 = 0.9f, b2 = 0.999f, eps = 0.00000001f, wd = 0.01f, c1 = 0.1f, c2 = 0.001f;
  float *w = mb_zeros(N), *g = mb_zeros(N), *m = mb_zeros(N), *v = mb_zeros(N);
  mb_rand_s(w, N, 1, 0.02f);
  float p1 = 1.0f, p2 = 1.0f;
  for (uint32_t t = 1; t <= 8; t++) {
    mb_rand_s(g, N, 100 + t, 0.001f);
    const float q1 = 1.0f - p1 * b1, q2 = 1.0f - p2 * b2;
    const float step = lr / q1, bc2 = (float)sqrt((double)q2), decay = 1.0f - lr * wd;
    for (size_t i = 0; i < N; i++) {
      float gi = g[i];
      float nm = m[i] + c1 * (gi - m[i]);
      float nv = v[i] * b2 + (c2 * gi) * gi;
      w[i] = w[i] * decay + (-step * nm) / ((float)sqrt((double)nv) / bc2 + eps);
      m[i] = nm; v[i] = nv; g[i] = 0.0f;
    }
    p1 = p1 * b1; p2 = p2 * b2;
  }
  mb_show_hash(w, N); mb_show_hash(m, N); mb_show_hash(v, N);
  return 0;
}
