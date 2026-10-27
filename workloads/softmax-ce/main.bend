# softmax-ce: tensor-array's softmax cross entropy over SmolLM2's vocabulary (49,152 logits a row, 64 rows), the loss
# of a language model's head: exp, max, sum and division, the F32 work that is not a product. 6 rounds, each on fresh
# logits (a gradient fed back as logits is near zero, and exp near zero is not the work of a real head). Prints each
# round's loss bits and the hash of the gradients' sum.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
import ../../lib/mb.bend as MB
import ../../lib/ta.bend as TT

def label(+i: U32) -> Nat:
  U32.to_nat(((((i * 2654435761 : U32) >> 7n) : U32) % 49152 : U32))

def labels_go(left: Nat, +i: U32, acc: List<&2, Nat>) -> List<&2, Nat>:
  match left:
    case Zero{}: acc
    case Succ{q}: labels_go(q, (i + 1 : U32), Con{label(i), acc})

def next_print(r: TA.MCE<64n, 49152n>) -> IO(TA.Mat<64n, 49152n>):
  match r:
    case TA.MCE{loss, grad}:
      do IO<TA.Mat<64n, 49152n>>:
        IO.print(U32.show(MB.f2u(loss)))
        return grad

def add_fin(r: TA.MPair<64n, 49152n>) -> TA.Mat<64n, 49152n>:
  match r:
    case TA.MPair{a, b}: a

# acc + the gradient of fresh logits under seed
def go(left: Nat, +seed: U32, acc: TA.Mat<64n, 49152n>) -> IO(Unit):
  match left:
    case Zero{}: TT.show_c(64n, 49152n, acc)
    case Succ{q}:
      do IO<Unit>:
        g : TA.Mat<64n, 49152n> <- next_print(TA.Mat.softmax_ce(64n, 49152n, TT.rmat(64n, 49152n, seed), labels_go(64n, seed, Nil{})))
        go(q, (seed + 1 : U32), add_fin(TA.Mat.add(64n, 49152n, acc, g)))

def main() -> IO(Unit):
  go(6n, 7, TA.Mat.zeros(64n, 49152n))
