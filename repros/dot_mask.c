// dot_mask.bend in C: the same rotating dot over the same arrays, 4096 times, the same bits. clang -std=c11 -O3.
#include "../lib/mb.h"

static float dot(const float *a, const float *b, int k) {
  float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
  for (int p = 0; p < k; p++) {
    float t = a0 + a[p] * b[p];
    a0 = a1; a1 = a2; a2 = a3; a3 = t;
  }
  return (a0 + a1) + (a2 + a3);
}

int main(void) {
  float *a = mb_zeros(65536), *b = mb_zeros(65536);
  mb_rand(a, 65536, 1); mb_rand(b, 65536, 2);
  // go adds round q's dot to acc at round q + 1, starting from the R's 0.0: 4096 rounds add 0 then 4095 dots
  float acc = 0.0f, s = 0.0f;
  for (int q = 0; q < 4096; q++) { acc = acc + s; s = dot(a, b, 65536); }
  printf("%u\n", f2u(acc));
  return 0;
}
