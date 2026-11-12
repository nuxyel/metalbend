# llama-token: whole tokens of a Llama, as llama.bend generates them: bend-ml-llama's forward pass (RMSNorm, the q/k/v
# products, RoPE, grouped-query attention over the key/value cache, the output product, SwiGLU, the residuals, the
# final norm and the tied head) at SmolLM2-135M's widths, with 2 layers and a vocabulary of 3,072, so that the head is
# a fifth of a token's products as in the 135M, on weights from lib/mb.bend. 32 positions through the cache, one token
# each; 283 M multiply-adds in the matrix products. Prints the hash of every position's logits.
import Base
import bend-ml-tensor-array@0.1.20.0/main.bend as TA
import bend-ml-llama@0.2.1.1/main.bend as M
import ../../lib/mb.bend as MB

# SmolLM2-135M's widths (3 key/value heads of 3 query heads each, heads of 64, a hidden size of 576, an inner width of
# 1,536, RMSNorm's epsilon and RoPE's base), with 2 layers and 3,072 tokens
def cfg() -> M.Cfg:
  M.Cfg{3n, 3n, 32n, 1536n, 2n, 3072n, 0.00001, 100000.0}

# ---- the weights: cell i of a matrix is its seed's value i times s, whatever bands hold it ----

def fill_go(left: Nat, +seed: U32, +s: F32, +off: U32, +i: U32, a: Array<F32>) -> Array<F32>:
  match left:
    case 0n:
      a
    case 1n+q:
      fill_go(q, seed, s, off, (i + 1 : U32), Array.set(F32, a, i, (MB.val(seed, (off + i : U32)) * s : F32)))

# a band's n cells: the matrix's cells off .. off + n - 1
def lfill(+n: Nat, +seed: U32, +s: F32, +off: U32, -r: Nat, -c: Nat, m: TA.Mat<r, c>) -> TA.Mat<r, c>:
  match m:
    case TA.Mat{d}:
      TA.Mat{fill_go(n, seed, s, off, 0, d)}

# every band filled from the matrix's own cells: off is the index of the band's first cell, so the weights do not
# depend on how many bands there are; rr is r's value (r itself is erased, as in tensor-array's bmv)
def bfill(+c: Nat, -r: Nat, b: TA.Bands<r, c>, +rr: Nat, -e: {rr == r : Nat}, +seed: U32, +s: F32, +off: U32) -> TA.Bands<r, c>:
  match b:
    case TA.BLeaf{m}:
      TA.BLeaf{lfill(Nat.mul(rr, c), seed, s, off, r, c, m)}
    case TA.BNode{x, y}:
      TA.BNode{bfill(c, TA.half(r), x, TA.half(rr), TA.eq_half(rr, r, e), seed, s, off), bfill(c, Nat.sub(r, TA.half(r)), y, Nat.sub(rr, TA.half(rr)), TA.eq_rest(rr, r, e), seed, s, (off + U32.from_nat(Nat.mul(TA.half(rr), c)) : U32))}

# an r x c matrix in 2^d bands
def bands(+d: Nat, +r: Nat, +c: Nat, +seed: U32, +s: F32) -> TA.Bands<r, c>:
  bfill(c, r, TA.Bands.zeros(d, r, c), r, {==}, seed, s, 0)

# a norm's n gains, around 1: 1 + 0.2 · value i of the seed
def gains(n: Nat, +seed: U32, +i: U32) -> List<&2, F32>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      (1.0 + (MB.val(seed, i) * 0.2 : F32) : F32) <> gains(p, seed, (i + 1 : U32))

# layer i's weights, seeds 16·i + 16 .. 16·i + 24: a product's weights are scaled so that it keeps its input's size
# (3.464 / sqrt(columns): 0.1443 for 576 columns, 0.0884 for 1,536)
def layer(+c: M.Cfg, +d: Nat, +sd: U32) -> M.LW<c>:
  M.LW{gains(M.Cfg.dim(c), sd, 0), bands(d, M.Cfg.dim(c), M.Cfg.dim(c), (sd + 1 : U32), 0.1443), bands(d, M.Cfg.kvw(c), M.Cfg.dim(c), (sd + 2 : U32), 0.1443), bands(d, M.Cfg.kvw(c), M.Cfg.dim(c), (sd + 3 : U32), 0.1443), bands(d, M.Cfg.dim(c), M.Cfg.dim(c), (sd + 4 : U32), 0.1443), gains(M.Cfg.dim(c), (sd + 5 : U32), 0), bands(d, M.Cfg.ffn(c), M.Cfg.dim(c), (sd + 6 : U32), 0.1443), bands(d, M.Cfg.ffn(c), M.Cfg.dim(c), (sd + 7 : U32), 0.1443), bands(d, M.Cfg.dim(c), M.Cfg.ffn(c), (sd + 8 : U32), 0.0884)}

def layers(n: Nat, +c: M.Cfg, +d: Nat, +sd: U32) -> List<&1, M.LW<c>>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      layer(c, d, sd) <> layers(p, c, d, (sd + 16 : U32))

# the model at band depth d, as llama.bend's loader builds it: the embedding (seed 1, its values as they are) gets
# one more level of bands than the layers when there are bands at all; the final norm's gains are seed 2's
def model(+c: M.Cfg, +d: Nat) -> M.Model<c>:
  M.Model{d, bands(Nat.add(d, Nat.min(d, 1n)), M.Cfg.vocab(c), M.Cfg.dim(c), 1, 1.0), layers(M.Cfg.layers(c), c, d, 16), gains(M.Cfg.dim(c), 2, 0)}

# ---- the positions ----

# FNV-1a over the bits of a list, from the state h (lib/mb.bend's hash, for a list)
def lhash(xs: List<&2, F32>, +h: U32) -> U32:
  match xs:
    case Nil{}:
      h
    case Con{x, t}:
      lhash(t, ((h .^. MB.f2u(x)) * 16777619 : U32))

# position t's token: 911·t + 7 modulo the vocabulary
def tok_at(+t: Nat) -> Nat:
  Nat.mod(Nat.add(Nat.mul(t, 911n), 7n), 3072n)

# One token at each position t, t + 1, ..., as llama.bend's generation runs a token (forward_gen): the hash of each
# position's logits, in order. fuel counts the positions left, with t + fuel = cap (inv), which gives each step its
# proof that the cache has room (step_room); the forward pass is matched by Out.then, so the loop recurses inside its
# closure.
def go(fuel: Nat, +c: M.Cfg, -cap: Nat, +t: Nat, -inv: {Nat.add(t, fuel) == cap : Nat}, m: M.Model<c>, cs: List<&1, M.KV<cap, t>>) -> List<&2, U32>:
  match fuel:
    case 0n:
      Nil{}
    case 1n++p:
      M.Out.then(List<&2, U32>, c, cap, t, M.forward_gen(c, cap, t, m, cs, M.step_room(t, p, cap, inv), tok_at(t)), lg => nf => acts => cs2 => m2 =>
        lhash(lg, 2166136261) <> go(p, c, cap, 1n+t, M.step_inv(t, p, cap, inv), m2, cs2))

# n positions on the model of c at band depth d
def run(+c: M.Cfg, +d: Nat, +n: Nat) -> List<&2, U32>:
  go(n, c, n, 0n, {==}, model(c, d), M.caches(c, M.Cfg.layers(c), n))

def show(hs: List<&2, U32>) -> IO(Unit):
  match hs:
    case Nil{}:
      IO.pure(Unit, Unit{})
    case Con{h, t}:
      do IO<Unit>:
        IO.print(U32.show(h))
        show(t)

# the band depth is llama.bend's rule for the thread count (one band up to two threads, 16 above): the bits are the
# same on any count
def main() -> IO(Unit):
  do IO<Unit>:
    threads : U32 <- IO.thread_count()
    show(run(cfg(), M.depth_for(threads), 32n))
