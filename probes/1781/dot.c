#include <stdint.h>
#include <stdio.h>
#include <string.h>

static float a[65536], b[65536];

static float dot(int k) {
  float a0 = 0, a1 = 0, a2 = 0, a3 = 0;
  for (int p = 0; p < k; p++) {
    float t = a0 + a[p] * b[p];
    a0 = a1; a1 = a2; a2 = a3; a3 = t;
  }
  return (a0 + a1) + (a2 + a3);
}

int main(void) {
  for (uint32_t i = 0; i < 65536; i++) {
    a[i] = (float)((i * 7u) % 1000u) / 1000.0f - 0.5f;
    b[i] = (float)((i * 13u) % 1000u) / 1000.0f - 0.5f;
  }
  float acc = 0, s = 0;
  for (int q = 0; q < 4096; q++) { acc = acc + s; s = dot(65536); }
  uint32_t w; memcpy(&w, &acc, 4); printf("%u\n", w);
  return 0;
}
