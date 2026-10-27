// matvec-bands' target: the same weights (each band of 16 filled from its own seed, as bfill does), the same 24 tokens
// of x -> up · x -> down · (up · x), and tensor-array's scalar dot (dotr): each product goes to the first of four sums
// and the sums rotate, then (a0 + a1) + (a2 + a3). Built with Bend's flags: clang -std=c11 -O3.
#include "../../lib/mb.h"

// fills the r x c matrix w band by band: a node of r rows splits into floor(r / 2) and the rest, its children seeded
// 2s + 1 and 2s + 2, down d levels (tensor-array's Bands.zeros and main.bend's bfill)
static void bfill(float *w, int r, int c, int d, uint32_t seed, float s) {
  if (d == 0) { mb_rand_s(w, (size_t)r * c, seed, s); return; }
  int h = r / 2;
  bfill(w, h, c, d - 1, seed * 2 + 1, s);
  bfill(w + (size_t)h * c, r - h, c, d - 1, seed * 2 + 2, s);
}

// y = W · x, W r x c with one row per output
static void matvec(int r, int c, const float *w, const float *x, float *y) {
  for (int j = 0; j < r; j++) {
    const float *row = w + (size_t)j * c;
    float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
    for (int p = 0; p < c; p++) {
      float t = a0 + x[p] * row[p];
      a0 = a1; a1 = a2; a2 = a3; a3 = t;
    }
    y[j] = (a0 + a1) + (a2 + a3);
  }
}

int main(void) {
  float *up = mb_zeros((size_t)8192 * 2048), *down = mb_zeros((size_t)2048 * 8192);
  float *x = mb_zeros(2048), *h = mb_zeros(8192);
  bfill(up, 8192, 2048, 4, 1, 0.0765f);
  bfill(down, 2048, 8192, 4, 2, 0.0383f);
  mb_rand(x, 2048, 3);
  for (int t = 0; t < 24; t++) {
    matvec(8192, 2048, up, x, h);
    matvec(2048, 8192, down, h, x);
  }
  mb_show_hash(x, 2048);
  return 0;
}
