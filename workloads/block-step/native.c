// block-step's target: BendTorch's SmolLM2-135M decoder block (Residual(RMSNorm, attention), then Residual(RMSNorm,
// SwiGLU)), 512 rows, trained with AdamW under MSE for 2 steps on the same weights, inputs and targets, in BendTorch's
// order of operations (lib/bt.h); each loss's bits printed as T.F32.print prints them, then the hash of the final
// weights and moments (bt_show_state). A Residual adds x + f(x) and its input gradient as dy + dx_f; a Fork's input
// gradients are summed as dx_first + dx_second; the SwiGLU product is silu(gate) * up. Bend's flags:
// clang -std=c11 -O3.
#include "../../lib/bt.h"

enum { N = 512, D = 576, KVW = 192, FF = 1536, STEPS = 2 };

int main(void) {
  const bt_attn A = {8, 64, 3, 3, 64, 0.125f};
  bt_param g1 = bt_param_new(D), wq = bt_param_new(D * D), wk = bt_param_new(KVW * D), wv = bt_param_new(KVW * D),
           wo = bt_param_new(D * D), g2 = bt_param_new(D), wg = bt_param_new(FF * D), wu = bt_param_new(FF * D),
           wd = bt_param_new(D * FF);
  for (int j = 0; j < D; j++) g1.w[j] = 1.0f, g2.w[j] = 1.0f;
  bt_gen(wq.w, D * D, 1, BT_W_SCALE); bt_gen(wk.w, KVW * D, 2, BT_W_SCALE);
  bt_gen(wv.w, KVW * D, 3, BT_W_SCALE); bt_gen(wo.w, D * D, 4, BT_W_SCALE);
  bt_gen(wg.w, FF * D, 5, BT_W_SCALE); bt_gen(wu.w, FF * D, 6, BT_W_SCALE); bt_gen(wd.w, D * FF, 7, BT_W_SCALE);
  bt_rope_tab rq = bt_rope_new(64, 32, 100000.0f), rk = bt_rope_new(64, 32, 100000.0f);
  // the attention half
  float *x = mb_zeros(N * D), *t = mb_zeros(N * D), *h = mb_zeros(N * D), *q = mb_zeros(N * D);
  float *k = mb_zeros(N * KVW), *v = mb_zeros(N * KVW), *o = mb_zeros(N * D), *a = mb_zeros(N * D);
  float *d_o = mb_zeros(N * D), *dq = mb_zeros(N * D), *dk = mb_zeros(N * KVW), *dv = mb_zeros(N * KVW);
  float *dxq = mb_zeros(N * D), *dxk = mb_zeros(N * D), *dxv = mb_zeros(N * D), *dx1 = mb_zeros(N * D);
  float *p = mb_zeros(64 * 64), *gm = mb_zeros(64 * 64), *ka = mb_zeros(64 * 64), *va = mb_zeros(64 * 64);
  // the feed-forward half
  float *x1 = mb_zeros(N * D), *h2 = mb_zeros(N * D), *zg = mb_zeros(N * FF), *sg = mb_zeros(N * FF);
  float *u = mb_zeros(N * FF), *z = mb_zeros(N * FF), *y = mb_zeros(N * D), *dz = mb_zeros(N * FF);
  float *ds = mb_zeros(N * FF), *du = mb_zeros(N * FF), *dxg = mb_zeros(N * D), *dxu = mb_zeros(N * D);
  float *dx2 = mb_zeros(N * D), *dy1 = mb_zeros(N * D), *sq = mb_zeros(N * D), *dg = mb_zeros(D);
  bt_param *ps[] = {&g1, &wq, &wk, &wv, &wo, &g2, &wg, &wu, &wd};
  bt_train tr = {0.0f, 0.0f};
  for (uint32_t s = 0; s < STEPS; s++) {
    bt_gen(x, N * D, 1000 + s, BT_X_SCALE);
    bt_gen(t, N * D, 2000 + s, BT_X_SCALE);
    // forward, the attention half: x1 = x + att(rms(x))
    bt_rms_fwd(N, D, 0.00001f, g1.w, x, h);
    bt_lin_fwd(N, D, D, wq.w, h, q);
    bt_lin_fwd(N, D, KVW, wk.w, h, k);
    bt_lin_fwd(N, D, KVW, wv.w, h, v);
    bt_rope(1, &rq, N, D, 9, q);
    bt_rope(1, &rk, N, KVW, 3, k);
    bt_attn_fwd(&A, q, k, v, o, p);
    bt_lin_fwd(N, D, D, wo.w, o, a);
    for (size_t i = 0; i < N * D; i++) x1[i] = x[i] + a[i];
    // the feed-forward half: y = x1 + down(silu(gate(rms(x1))) * up(rms(x1)))
    bt_rms_fwd(N, D, 0.00001f, g2.w, x1, h2);
    bt_lin_fwd(N, D, FF, wg.w, h2, zg);
    for (size_t i = 0; i < N * FF; i++) sg[i] = bt_silu(zg[i]);
    bt_lin_fwd(N, D, FF, wu.w, h2, u);
    for (size_t i = 0; i < N * FF; i++) z[i] = sg[i] * u[i];
    bt_lin_fwd(N, FF, D, wd.w, z, y);
    for (size_t i = 0; i < N * D; i++) y[i] = x1[i] + y[i];
    float l = bt_mse(N * D, y, t, sq);
    // backward, the feed-forward half (y holds dy)
    bt_lin_bwd(N, FF, D, wd.w, z, y, dz, wd.g);
    for (size_t i = 0; i < N * FF; i++) { ds[i] = dz[i] * u[i]; du[i] = dz[i] * sg[i]; }
    bt_lin_bwd(N, D, FF, wu.w, h2, du, dxu, wu.g);
    for (size_t i = 0; i < N * FF; i++) ds[i] = bt_silu_d(ds[i], zg[i]);
    bt_lin_bwd(N, D, FF, wg.w, h2, ds, dxg, wg.g);
    bt_add(N * D, dxg, dxu);
    bt_rms_bwd(N, D, 0.00001f, g2.w, x1, dxg, dx2, dg, g2.g);
    for (size_t i = 0; i < N * D; i++) dy1[i] = y[i] + dx2[i];
    // the attention half
    bt_lin_bwd(N, D, D, wo.w, o, dy1, d_o, wo.g);
    bt_attn_bwd(&A, q, k, v, d_o, dq, dk, dv, p, gm, ka, va);
    bt_rope(0, &rk, N, KVW, 3, dk);
    bt_rope(0, &rq, N, D, 9, dq);
    bt_lin_bwd(N, D, KVW, wv.w, h, dv, dxv, wv.g);
    bt_lin_bwd(N, D, KVW, wk.w, h, dk, dxk, wk.g);
    bt_add(N * D, dxk, dxv);
    bt_lin_bwd(N, D, D, wq.w, h, dq, dxq, wq.g);
    bt_add(N * D, dxq, dxk);
    bt_rms_bwd(N, D, 0.00001f, g1.w, x, dxq, dx1, dg, g1.g);
    // the block's input gradient, dy1 + dx1, is computed and dropped, as Train.step drops it
    bt_add(N * D, dy1, dx1);
    // the step
    bt_opt op = bt_opt_next(&tr);
    for (int i = 0; i < 9; i++) bt_adam(&op, ps[i]->n, ps[i]->w, ps[i]->g, ps[i]->m, ps[i]->v);
    printf("loss %u\n", f2u(l));
  }
  bt_show_state(ps, 9);
  printf("done\n");
  return 0;
}
