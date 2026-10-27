# adamw: BendTorch v1.1.1's AdamW update (T.Opt.mat, the loop every training step runs over every weight) alone, on a
# matrix the size of SmolLM2-135M's embedding (49,152 x 576, 28.3 M weights), 8 steps, each on a fresh gradient.
# PyTorch's order of operations (torch/main.bend's adam_l); bias corrections from b1^t and b2^t carried in F32.
# Prints the hash of the weights and of both moments.
import Base
import bendtorch@1.1.1.0/main.bend as T
import bend-ml-tensor-array@0.1.14.0/main.bend as TA
import ../../lib/mb.bend as MB

def N() -> Nat:
  28311552n

def M() -> Type:
  TA.Mat<49152n, 576n>

def cfg() -> T.OptCfg:
  T.CAdamW{0.001, 0.9, 0.999, 0.00000001, 0.01, 0.1, 0.001}

def fill(+seed: U32, +s: F32, m: M) -> M:
  match m:
    case TA.Mat{d}: TA.Mat{MB.rand_s(N(), seed, s, d)}

def show_m(m: M) -> IO(Unit):
  match m:
    case TA.Mat{d}: MB.show_hash(MB.hash(N(), d))

def show(r: T.MatStep<49152n, 576n>) -> IO(Unit):
  match r:
    case T.MatStep{w, g, T.TwoMom{m, v}}:
      do IO<Unit>:
        show_m(w)
        show_m(m)
        show_m(v)
    case T.MatStep{w, g, st}: IO.print("no moments")

# step t (from 1): p1 = b1^t and p2 = b2^t, the gradient refilled (the update zeroes it)
def go(left: Nat, +t: U32, +p1: F32, +p2: F32, r: T.MatStep<49152n, 576n>) -> IO(Unit):
  match left r:
    case 0n _: show(r)
    case 1n+q T.MatStep{w, g, st}: go(q, (t + 1 : U32), (p1 * 0.9 : F32), (p2 * 0.999 : F32), T.Opt.mat(49152n, 576n, T.Opt.at(cfg(), (1.0 - (p1 * 0.9 : F32) : F32), (1.0 - (p2 * 0.999 : F32) : F32)), w, fill((100 + t : U32), 0.001, g), st))

def main() -> IO(Unit):
  go(8n, 1, 1.0, 1.0, T.MatStep{fill(1, 0.02, TA.Mat.zeros(49152n, 576n)), TA.Mat.zeros(49152n, 576n), T.TwoMom{TA.Mat.zeros(49152n, 576n), TA.Mat.zeros(49152n, 576n)}})
