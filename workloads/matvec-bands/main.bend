# matvec-bands: SmolLM2-1.7B's feed-forward products at one token, as llama.bend runs them in decoding: tensor-array's
# Bands (16 bands, matrix · vector without copying the weights), x (2048) -> up (8192 x 2048) -> down (2048 x 8192),
# 24 times, each output the next input. 805 M multiply-adds. Prints the hash of the last x.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
import ../../lib/mb.bend as MB
import ../../lib/ta.bend as TT

def lfill(+n: Nat, +seed: U32, +s: F32, -r: Nat, -c: Nat, m: TA.Mat<r, c>) -> TA.Mat<r, c>:
  match m:
    case TA.Mat{d}: TA.Mat{MB.rand_s(n, seed, s, d)}

# every band filled with its own seed, scaled by s; rr is r's value (r itself is erased, so the call that shrinks b
# comes first, as tensor-array's bmv does)
def bfill(+c: Nat, -r: Nat, b: TA.Bands<r, c>, +rr: Nat, -e: {rr == r : Nat}, +seed: U32, +s: F32) -> TA.Bands<r, c>:
  match b:
    case TA.BLeaf{m}: TA.BLeaf{lfill(Nat.mul(rr, c), seed, s, r, c, m)}
    case TA.BNode{x, y}: TA.BNode{bfill(c, TA.half(r), x, TA.half(rr), TA.eq_half(rr, r, e), ((seed * 2 : U32) + 1 : U32), s), bfill(c, Nat.sub(r, TA.half(r)), y, Nat.sub(rr, TA.half(rr)), TA.eq_rest(rr, r, e), ((seed * 2 : U32) + 2 : U32), s)}

type W is Type:
  W{up: TA.Bands<8192n, 2048n>, down: TA.Bands<2048n, 8192n>, x: TA.Mat<1n, 2048n>}

def down_fin(up: TA.Bands<8192n, 2048n>, r: TA.BV<2048n, 8192n>) -> W:
  match r:
    case TA.BV{down, x}: W{up, down, x}

def up_fin(down: TA.Bands<2048n, 8192n>, r: TA.BV<8192n, 2048n>) -> W:
  match r:
    case TA.BV{up, h}: down_fin(up, TA.Bands.matvec(2048n, 8192n, down, h))

# one token: x -> up · x -> down · (up · x)
def step(w: W) -> W:
  match w:
    case W{up, down, x}: up_fin(down, TA.Bands.matvec(8192n, 2048n, up, x))

def go(left: Nat, w: W) -> IO(Unit):
  match left w:
    case Zero{} W{up, down, x}: TT.show_c(1n, 2048n, x)
    case Succ{q} _: go(q, step(w))

def main() -> IO(Unit):
  go(24n, W{bfill(2048n, 8192n, TA.Bands.zeros(4n, 8192n, 2048n), 8192n, {==}, 1, 0.0765), bfill(8192n, 2048n, TA.Bands.zeros(4n, 2048n, 8192n), 2048n, {==}, 2, 0.0383), TT.rmat(1n, 2048n, 3)})
