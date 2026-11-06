// attention-step's target: the block's attention half (RMSNorm, the q/k/v projections, RoPE, grouped-query causal
// attention, the output projection) at SmolLM2-135M's sizes, 512 rows, trained with AdamW under MSE for 4 steps on the
// same weights, inputs and targets, in BendTorch's order of operations (lib/bt.h); each loss's bits printed as
// T.F32.print prints them, then the hash of the final weights and moments (bt_show_state). A Fork's input gradients
// are summed as dx_q + (dx_k + dx_v). Bend's flags: clang -std=c11 -O3.
#include "../../lib/bt.h"

enum { N = 512, D = 576, KVW = 192, STEPS = 4 };

int main(void) {
  const bt_attn A = {8, 64, 3, 3, 64, 0.125f};
  bt_param gain = bt_param_new(D), wq = bt_param_new(D * D), wk = bt_param_new(KVW * D), wv = bt_param_new(KVW * D),
           wo = bt_param_new(D * D);
  for (int j = 0; j < D; j++) gain.w[j] = 1.0f;
  bt_gen(wq.w, D * D, 1, BT_W_SCALE); bt_gen(wk.w, KVW * D, 2, BT_W_SCALE);
  bt_gen(wv.w, KVW * D, 3, BT_W_SCALE); bt_gen(wo.w, D * D, 4, BT_W_SCALE);
  bt_rope_tab rq = bt_rope_new(64, 32, 100000.0f), rk = bt_rope_new(64, 32, 100000.0f);
  float *x = mb_zeros(N * D), *t = mb_zeros(N * D), *h = mb_zeros(N * D), *q = mb_zeros(N * D);
  float *k = mb_zeros(N * KVW), *v = mb_zeros(N * KVW), *o = mb_zeros(N * D), *y = mb_zeros(N * D);
  float *sq = mb_zeros(N * D), *d_o = mb_zeros(N * D), *dq = mb_zeros(N * D), *dk = mb_zeros(N * KVW);
  float *dv = mb_zeros(N * KVW), *dxq = mb_zeros(N * D), *dxk = mb_zeros(N * D), *dxv = mb_zeros(N * D);
  float *dx = mb_zeros(N * D), *dg = mb_zeros(D), *p = mb_zeros(64 * 64), *gm = mb_zeros(64 * 64);
  float *ka = mb_zeros(64 * 64), *va = mb_zeros(64 * 64);
  bt_train tr = {0.0f, 0.0f};
  for (uint32_t s = 0; s < STEPS; s++) {
    bt_gen(x, N * D, 1000 + s, BT_X_SCALE);
    bt_gen(t, N * D, 2000 + s, BT_X_SCALE);
    // forward
    bt_rms_fwd(N, D, 0.00001f, gain.w, x, h);
    bt_lin_fwd(N, D, D, wq.w, h, q);
    bt_lin_fwd(N, D, KVW, wk.w, h, k);
    bt_lin_fwd(N, D, KVW, wv.w, h, v);
    bt_rope(1, &rq, N, D, 9, q);
    bt_rope(1, &rk, N, KVW, 3, k);
    bt_attn_fwd(&A, q, k, v, o, p);
    bt_lin_fwd(N, D, D, wo.w, o, y);
    float l = bt_mse(N * D, y, t, sq);
    // backward (y holds dy)
    bt_lin_bwd(N, D, D, wo.w, o, y, d_o, wo.g);
    bt_attn_bwd(&A, q, k, v, d_o, dq, dk, dv, p, gm, ka, va);
    bt_rope(0, &rk, N, KVW, 3, dk);
    bt_rope(0, &rq, N, D, 9, dq);
    bt_lin_bwd(N, D, KVW, wv.w, h, dv, dxv, wv.g);
    bt_lin_bwd(N, D, KVW, wk.w, h, dk, dxk, wk.g);
    bt_add(N * D, dxk, dxv);
    bt_lin_bwd(N, D, D, wq.w, h, dq, dxq, wq.g);
    bt_add(N * D, dxq, dxk);
    bt_rms_bwd(N, D, 0.00001f, gain.w, x, dxq, dx, dg, gain.g);
    // the step
    bt_opt op = bt_opt_next(&tr);
    bt_adam(&op, D, gain.w, gain.g, gain.m, gain.v);
    bt_adam(&op, D * D, wq.w, wq.g, wq.m, wq.v);
    bt_adam(&op, KVW * D, wk.w, wk.g, wk.m, wk.v);
    bt_adam(&op, KVW * D, wv.w, wv.g, wv.m, wv.v);
    bt_adam(&op, D * D, wo.w, wo.g, wo.m, wo.v);
    printf("loss %u\n", f2u(l));
  }
  bt_param *ps[] = {&gain, &wq, &wk, &wv, &wo};
  bt_show_state(ps, 5);
  printf("done\n");
  return 0;
}
