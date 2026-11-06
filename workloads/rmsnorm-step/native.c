// rmsnorm-step's target: one RMSNorm (512 rows of 576, eps 1e-5, its gain from ones) trained with AdamW under MSE for
// 200 steps on the same inputs and targets, in BendTorch's order of operations (lib/bt.h): forward, the loss, backward
// (dx is computed and dropped, as the layer computes it), the step; each loss's bits printed as T.F32.print prints
// them, then the hash of the final weights and moments (bt_show_state). Bend's flags: clang -std=c11 -O3.
#include "../../lib/bt.h"

enum { N = 512, D = 576, STEPS = 200 };

int main(void) {
  bt_param gain = bt_param_new(D);
  for (int j = 0; j < D; j++) gain.w[j] = 1.0f;
  float *x = mb_zeros(N * D), *t = mb_zeros(N * D), *y = mb_zeros(N * D), *q = mb_zeros(N * D);
  float *dx = mb_zeros(N * D), *dg = mb_zeros(D);
  bt_train tr = {0.0f, 0.0f};
  for (uint32_t s = 0; s < STEPS; s++) {
    bt_gen(x, N * D, 1000 + s, BT_X_SCALE);
    bt_gen(t, N * D, 2000 + s, BT_X_SCALE);
    bt_rms_fwd(N, D, 0.00001f, gain.w, x, y);
    float l = bt_mse(N * D, y, t, q);
    bt_rms_bwd(N, D, 0.00001f, gain.w, x, y, dx, dg, gain.g);
    bt_opt o = bt_opt_next(&tr);
    bt_adam(&o, D, gain.w, gain.g, gain.m, gain.v);
    printf("loss %u\n", f2u(l));
  }
  bt_param *ps[] = {&gain};
  bt_show_state(ps, 1);
  printf("done\n");
  return 0;
}
