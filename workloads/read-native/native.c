// read-native's target (and read-binary's): data/dense.bin read with one fread into an array of F32, then hashed.
// Bend's flags: clang -std=c11 -O3.
#include "../../lib/mb.h"

enum { N = 4194304 };

int main(void) {
  float *a = mb_zeros(N);
  FILE *f = fopen("data/dense.bin", "rb");
  if (!f || fread(a, sizeof(float), N, f) != N) { perror("data/dense.bin"); return 1; }
  fclose(f);
  mb_show_hash(a, N);
  return 0;
}
