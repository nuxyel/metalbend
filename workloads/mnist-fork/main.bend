# mnist-fork: mnist-step's training step (the 784-128-10 MLP of bend-ml's MNIST demo, batch 100, SGD at lr 0.1, 200
# steps on the same synthetic batches) with its five products through tensor-fork 0.1.5.0, whose parallel blocks
# share their operands instead of cloning them (BendTorch's fast layers take the same path), on tensor-array 0.1.18.0.
# Every other operation is tensor-array's. Must print mnist-step's hashes: tensor-fork keeps tensor-array's bits.
import Base
import bend-ml-tensor-array@0.1.18.0/main.bend as TA
import bend-ml-tensor-fork@0.1.5.0/main.bend as TF
import ../../lib/mb.bend as MB
import ../../lib/ta18.bend as TT

# parameters and training step (batch of 100)
# ---------------------------------------------------------------------

type Pm is Type:
  Pm{w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>}

type St2 is Type:
  St2{loss: F32, pm: Pm}

# 4. SGD on the four parameters

def u4(loss: F32, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, r: TA.MPair<1n, 10n>) -> St2:
  match r:
    case TA.MPair{b2, db2}:
      St2{loss, Pm{w1, b1, w2, b2}}

def u3(+lr: F32, loss: F32, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, r: TA.MPair<128n, 10n>) -> St2:
  match r:
    case TA.MPair{w2, dw2}:
      u4(loss, w1, b1, w2, TA.Mat.sgd(1n, 10n, lr, b2, db2))

def u2(+lr: F32, loss: F32, w1: TA.Mat<784n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, r: TA.MPair<1n, 128n>) -> St2:
  match r:
    case TA.MPair{b1, db1}:
      u3(lr, loss, w1, b1, b2, db2, TA.Mat.sgd(128n, 10n, lr, w2, dw2))

def u1(+lr: F32, loss: F32, b1: TA.Mat<1n, 128n>, db1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, r: TA.MPair<784n, 128n>) -> St2:
  match r:
    case TA.MPair{w1, dw1}:
      u2(lr, loss, w1, w2, dw2, b2, db2, TA.Mat.sgd(1n, 128n, lr, b1, db1))

# 3. gradient of the first layer: dW1 = Xᵀ · dZ1 (784 x 128), db1 = sum of the rows of dZ1

def s13(+lr: F32, loss: F32, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, dw1: TA.Mat<784n, 128n>, r: TA.MColSum<100n, 128n>) -> St2:
  match r:
    case TA.MColSum{dz1, db1}:
      u1(lr, loss, b1, db1, w2, dw2, b2, db2, TA.Mat.sgd(784n, 128n, lr, w1, dw1))

def s12(+lr: F32, loss: F32, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, r: TA.MMulTN<784n, 100n, 128n>) -> St2:
  match r:
    case TA.MMulTN{x, dz1, dw1}:
      s13(lr, loss, w1, b1, w2, dw2, b2, db2, dw1, TA.Mat.col_sums(100n, 128n, dz1))

def s11(+lr: F32, loss: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, db2: TA.Mat<1n, 10n>, r: TA.MPair<100n, 128n>) -> St2:
  match r:
    case TA.MPair{dz1, h}:
      s12(lr, loss, w1, b1, w2, dw2, b2, db2, TF.matmul_tn(784n, 100n, 128n, 3n, x, dz1))

# 2. gradients of the second layer and of the relu

def s10(+lr: F32, loss: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, h: TA.Mat<100n, 128n>, dh: TA.Mat<100n, 128n>, r: TA.MColSum<100n, 10n>) -> St2:
  match r:
    case TA.MColSum{g2, db2}:
      s11(lr, loss, x, w1, b1, w2, dw2, b2, db2, TA.Mat.relu_bwd(100n, 128n, dh, h))

def s9(+lr: F32, loss: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, dw2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, h: TA.Mat<100n, 128n>, r: TA.MMulNT<100n, 10n, 128n>) -> St2:
  match r:
    case TA.MMulNT{g2, w2, dh}:
      s10(lr, loss, x, w1, b1, w2, dw2, b2, h, dh, TA.Mat.col_sums(100n, 10n, g2))

def s8(+lr: F32, loss: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, r: TA.MMulTN<128n, 100n, 10n>) -> St2:
  match r:
    case TA.MMulTN{h, g2, dw2}:
      s9(lr, loss, x, w1, b1, dw2, b2, h, TF.matmul_nt(100n, 10n, 128n, 0n, g2, w2))

# 1. forward of the second layer and the loss

def s7(+lr: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, h: TA.Mat<100n, 128n>, w2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, r: TA.MCE<100n, 10n>) -> St2:
  match r:
    case TA.MCE{loss, g2}:
      s8(lr, loss, x, w1, b1, w2, b2, TF.matmul_tn(128n, 100n, 10n, 0n, h, g2))

def s6(+lr: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, h: TA.Mat<100n, 128n>, w2: TA.Mat<128n, 10n>, labels: List<&2, Nat>, r: TA.MBias<100n, 10n>) -> St2:
  match r:
    case TA.MBias{z2, b2}:
      s7(lr, x, w1, b1, h, w2, b2, TA.Mat.softmax_ce(100n, 10n, z2, labels))

def s5(+lr: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, b2: TA.Mat<1n, 10n>, labels: List<&2, Nat>, r: TA.MMul<100n, 128n, 10n>) -> St2:
  match r:
    case TA.MMul{h, w2, z2}:
      s6(lr, x, w1, b1, h, w2, labels, TA.Mat.add_row(100n, 10n, z2, b2))

def s4(+lr: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, b1: TA.Mat<1n, 128n>, w2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, labels: List<&2, Nat>, h: TA.Mat<100n, 128n>) -> St2:
  s5(lr, x, w1, b1, b2, labels, TF.matmul(100n, 128n, 10n, 0n, h, w2))

# 0. forward of the first layer

def s3(+lr: F32, x: TA.Mat<100n, 784n>, w1: TA.Mat<784n, 128n>, w2: TA.Mat<128n, 10n>, b2: TA.Mat<1n, 10n>, labels: List<&2, Nat>, r: TA.MBias<100n, 128n>) -> St2:
  match r:
    case TA.MBias{z1, b1}:
      s4(lr, x, w1, b1, w2, b2, labels, TA.Mat.relu(100n, 128n, z1))

def s2(+lr: F32, w2: TA.Mat<128n, 10n>, b1: TA.Mat<1n, 128n>, b2: TA.Mat<1n, 10n>, labels: List<&2, Nat>, r: TA.MMul<100n, 784n, 128n>) -> St2:
  match r:
    case TA.MMul{x, w1, z1}:
      s3(lr, x, w1, w2, b2, labels, TA.Mat.add_row(100n, 128n, z1, b1))

def step(pm: Pm, x: TA.Mat<100n, 784n>, labels: List<&2, Nat>, +lr: F32) -> St2:
  match pm:
    case Pm{w1, b1, w2, b2}:
      s2(lr, w2, b1, b2, labels, TF.matmul(100n, 784n, 128n, 3n, x, w1))

# ---------------------------------------------------------------------
# synthetic data
# ---------------------------------------------------------------------

def label(+seed: U32, +i: U32) -> Nat:
  U32.to_nat((((((i + seed : U32) * 2654435761 : U32) >> 7n) : U32) % 10 : U32))

def labels_go(left: Nat, +seed: U32, +i: U32, acc: List<&2, Nat>) -> List<&2, Nat>:
  match left:
    case Zero{}: acc
    case Succ{q}: labels_go(q, seed, (i + 1 : U32), Con{label(seed, i), acc})

def wmat2(+n: Nat, +seed: U32, +s: F32, -r: Nat, -c: Nat, m: TA.Mat<r, c>) -> TA.Mat<r, c>:
  match m:
    case TA.Mat{d}: TA.Mat{MB.rand_s(n, seed, s, d)}

# an r x c weight matrix of seed's values times s
def wmat(+r: Nat, +c: Nat, +seed: U32, +s: F32) -> TA.Mat<r, c>:
  wmat2(Nat.mul(r, c), seed, s, r, c, TA.Mat.zeros(r, c))

def tloop(k: Nat, +b: U32, +lr: F32, acc: F32, r: St2) -> St2:
  match k r:
    case 0n St2{l, pm}: St2{(acc + l : F32), pm}
    case 1n+p St2{l, pm}: tloop(p, (b + 1 : U32), lr, (acc + l : F32), step(pm, TT.rmat(100n, 784n, (1000 + b : U32)), labels_go(100n, (b * 100 : U32), 0, Nil{}), lr))

def report(r: St2) -> IO(Unit):
  match r:
    case St2{loss, pm}:
      match pm:
        case Pm{w1, b1, w2, b2}:
          do IO<Unit>:
            IO.print(U32.show(MB.f2u(loss)))
            TT.show_c(784n, 128n, w1)
            TT.show_c(1n, 128n, b1)
            TT.show_c(128n, 10n, w2)
            TT.show_c(1n, 10n, b2)

def main() -> IO(Unit):
  report(tloop(200n, 0, 0.1, 0.0, St2{0.0, Pm{wmat(784n, 128n, 1, 0.124), TA.Mat.zeros(1n, 128n), wmat(128n, 10n, 2, 0.306), TA.Mat.zeros(1n, 10n)}}))
