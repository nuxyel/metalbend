// bpe-encode's target: minbpe's byte-level BPE as a C programmer writes it, on main.bend's two texts. Training: the
// adjacent pairs counted in a table indexed by the two ids, the most frequent pair taken (on a tie, the one that first
// appears in the text), every occurrence merged left to right without overlap into a new id, TRAIN times. Encoding:
// each rule applied in order to the second text. The same rules and tokens as bend-ml-bpe-tokenizer, so the same
// output. Bend's flags: clang -std=c11 -O3.
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { TRAIN = 256, TRAIN_WORDS = 4096, ENC_WORDS = 32768, V = 256 + TRAIN };

static uint32_t mix(uint32_t x) {
  uint32_t h = (x * 2654435761u) ^ (x >> 15);
  return (h * 2246822519u) ^ (h >> 13);
}

static uint32_t word(uint32_t seed, uint32_t i) {
  uint32_t k = seed + i * 2, a = mix(k) % 64, b = mix(k + 1) % 64;
  return a < b ? a : b;
}

// the text under seed, each word followed by a space; its length in *n
static uint32_t *text(uint32_t words, uint32_t seed, size_t *n) {
  uint32_t *t = malloc((size_t)words * 8 * sizeof *t);
  if (!t) { perror("malloc"); exit(1); }
  size_t m = 0;
  for (uint32_t i = 0; i < words; i++) {
    uint32_t w = word(seed, i), len = 2 + mix(w * 7 + 1) % 6;
    for (uint32_t j = 0; j < len; j++) t[m++] = 97 + mix(w * 131 + j * 17 + 5) % 12;
    t[m++] = 32;
  }
  *n = m;
  return t;
}

// every non-overlapping (a, b) of t, left to right, becomes c; the new length
static size_t merge(uint32_t *t, size_t n, uint32_t a, uint32_t b, uint32_t c) {
  size_t i = 0, o = 0;
  while (i < n) {
    if (i + 1 < n && t[i] == a && t[i + 1] == b) { t[o++] = c; i += 2; }
    else t[o++] = t[i++];
  }
  return o;
}

int main(void) {
  static uint32_t cnt[V * V], ra[TRAIN], rb[TRAIN];
  size_t n;
  uint32_t *t = text(TRAIN_WORDS, 1000003, &n);
  uint32_t *order = malloc(n * sizeof *order);
  int rules = 0;
  for (; rules < TRAIN && n >= 2; rules++) {
    // the pairs in the order they first appear, with their counts
    size_t np = 0;
    for (size_t i = 0; i + 1 < n; i++) {
      uint32_t p = t[i] * V + t[i + 1];
      if (cnt[p]++ == 0) order[np++] = p;
    }
    uint32_t best = order[0];
    for (size_t k = 1; k < np; k++) if (cnt[order[k]] > cnt[best]) best = order[k];
    for (size_t k = 0; k < np; k++) cnt[order[k]] = 0;
    ra[rules] = best / V, rb[rules] = best % V;
    n = merge(t, n, ra[rules], rb[rules], 256 + (uint32_t)rules);
  }
  free(t);
  t = text(ENC_WORDS, 2000003, &n);
  for (int r = 0; r < rules; r++) n = merge(t, n, ra[r], rb[r], 256 + (uint32_t)r);
  uint32_t h = 2166136261u;
  for (size_t i = 0; i < n; i++) h = (h ^ t[i]) * 16777619u;
  printf("%d\n%zu\n%u\n", rules, n, h);
  return 0;
}
