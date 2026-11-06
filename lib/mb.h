// MetalBend's shared pieces in C: lib/mb.bend's inputs and output hash, bit for bit.
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static inline uint32_t f2u(float x) { uint32_t u; memcpy(&u, &x, 4); return u; }
static inline float u2f(uint32_t u) { float x; memcpy(&x, &u, 4); return x; }

// mb.bend's val: a hash of i under seed, as a number in [-0.5, 0.5)
static inline float mb_val(uint32_t seed, uint32_t i) {
  uint32_t h = ((i + seed) * 2654435761u) ^ (i >> 13);
  uint32_t g = (h * 2246822519u) ^ (h >> 16);
  return u2f((g >> 9) | 1065353216u) - 1.5f;
}

static inline void mb_rand(float *a, size_t n, uint32_t seed) {
  for (size_t i = 0; i < n; i++) a[i] = mb_val(seed, (uint32_t)i);
}

static inline void mb_rand_s(float *a, size_t n, uint32_t seed, float s) {
  for (size_t i = 0; i < n; i++) a[i] = mb_val(seed, (uint32_t)i) * s;
}

// FNV-1a over the bits of n cells, from the state h: mb.bend's hash_go, which a hash over several arrays carries on
static inline uint32_t mb_fnv(uint32_t h, const float *a, size_t n) {
  for (size_t i = 0; i < n; i++) h = (h ^ f2u(a[i])) * 16777619u;
  return h;
}

#define MB_FNV_START 2166136261u

// mb.bend's hash of n cells, printed as its show_hash prints it
static inline void mb_show_hash(const float *a, size_t n) { printf("%u\n", mb_fnv(MB_FNV_START, a, n)); }

static inline float *mb_zeros(size_t n) {
  float *a = calloc(n, sizeof(float));
  if (!a) { perror("calloc"); exit(1); }
  return a;
}
