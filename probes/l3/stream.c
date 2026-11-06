// The antagonist: one thread that streams through its own buffer (BUF_MB, 64 MB by default, well past the 24 MB L3),
// reading and writing every 8 bytes, until SIGTERM; then it prints its rate in GB/s (read + write) to stderr. run.sh
// starts one per E-core that shares the P-cores' L3, each pinned with taskset, so the L3 and the memory bus stay busy
// while the measured program runs alone on CPU 3. Built with clang -O2.
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static volatile sig_atomic_t stop = 0;
static void on_term(int s) { (void)s; stop = 1; }

static double now(void) {
  struct timespec t;
  clock_gettime(CLOCK_MONOTONIC, &t);
  return t.tv_sec + t.tv_nsec * 1e-9;
}

int main(void) {
  const char *mb = getenv("BUF_MB");
  size_t n = (size_t)(mb ? atol(mb) : 64) << 17;  // MB -> 8-byte words
  uint64_t *a = malloc(n * sizeof *a);
  if (!a) return 1;
  for (size_t i = 0; i < n; i++) a[i] = i;
  signal(SIGTERM, on_term);
  signal(SIGINT, on_term);
  double t0 = now();
  uint64_t passes = 0;
  while (!stop) {
    for (size_t i = 0; i < n; i++) a[i] += 1;
    passes++;
  }
  double t = now() - t0;
  fprintf(stderr, "%.2f\n", t > 0 ? 2.0 * passes * n * sizeof *a / t / 1e9 : 0.0);
  return (int)(a[n / 2] & 0);
}
