// softmax-ce's target: tensor-array's Mat.softmax_ce on the same 6 rounds of fresh logits, in the same order of
// operations: per row the max (x < y ? y : x, from the first number), exp(h - max) through libm's double exp rounded
// to F32 (how Bend emits F32.exp), one running sum, the divisions, the loss minus log(max(p[label], 1e-12)), the gradient
// (p - onehot) / 64; the round's loss is divided by 64; the gradients summed into acc. Bend's flags: clang -std=c11 -O3.
#include "../../lib/mb.h"

enum { N = 64, C = 49152 };

static uint32_t label(uint32_t i) { return ((i * 2654435761u) >> 7) % 49152u; }

int main(void) {
  float *z = mb_zeros((size_t)N * C), *acc = mb_zeros((size_t)N * C), *e = mb_zeros(C);
  const float nf = (float)N;
  for (uint32_t seed = 7; seed < 7 + 6; seed++) {
    mb_rand(z, (size_t)N * C, seed);
    float loss = 0.0f;
    for (int i = 0; i < N; i++) {
      // labels_go builds its list by prepending, so row i takes the label of index seed + 63 - i
      uint32_t y = label(seed + (N - 1) - (uint32_t)i);
      float *row = z + (size_t)i * C;
      float m = row[0];
      for (int j = 1; j < C; j++) m = m < row[j] ? row[j] : m;
      for (int j = 0; j < C; j++) e[j] = (float)exp((double)(row[j] - m));
      float s = 0.0f;
      for (int j = 0; j < C; j++) s = s + e[j];
      for (int j = 0; j < C; j++) e[j] = e[j] / s;
      float py = e[y], lo = 0.000000000001f;
      loss = loss - (float)log((double)(py < lo ? lo : py));
      for (int j = 0; j < C; j++) row[j] = (e[j] - (j == (int)y ? 1.0f : 0.0f)) / nf;
    }
    printf("%u\n", f2u(loss / nf));
    for (size_t t = 0; t < (size_t)N * C; t++) acc[t] = acc[t] - (-1.0f * z[t]);
  }
  mb_show_hash(acc, (size_t)N * C);
  return 0;
}
