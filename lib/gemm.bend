# The three products of one SmolLM2-135M layer's feed-forward input at a batch of 256 tokens, each 226.5 M
# multiply-adds, repeated into one C (the accumulating forms). gemm.bend runs them through tensor-array, gemm_fork.bend
# through tensor-fork (the same bits).
#   nt: C(256 x 1536) += A(256 x 576) · B(1536 x 576)ᵀ     the forward product
#   tn: C(1536 x 576) += A(256 x 1536)ᵀ · B(256 x 576)     a weight gradient
#   nn: C(256 x 576)  += A(256 x 1536) · B(1536 x 576)     an input gradient
# Prints the hash of each C, in that order.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
import ./ta.bend as TT

def nt_step(+par: Nat, +n: Nat, +k: Nat, +m: Nat, a: TA.Mat<n, k>, b: TA.Mat<m, k>, c: TA.Mat<n, m>) -> TA.MMulNT<n, k, m>:
  TA.Mat.matmul_nt_acc(n, k, m, par, a, b, c)

def nt_go(left: Nat, +par: Nat, +n: Nat, +k: Nat, +m: Nat, r: TA.MMulNT<n, k, m>) -> IO(Unit):
  match left r:
    case Zero{} TA.MMulNT{a, b, c}: TT.show_c(n, m, c)
    case Succ{q} TA.MMulNT{a, b, c}: nt_go(q, par, n, k, m, nt_step(par, n, k, m, a, b, c))

def tn_step(+par: Nat, +n: Nat, +k: Nat, +m: Nat, a: TA.Mat<k, n>, b: TA.Mat<k, m>, c: TA.Mat<n, m>) -> TA.MMulTN<n, k, m>:
  TA.Mat.matmul_tn_acc(n, k, m, par, a, b, c)

def tn_go(left: Nat, +par: Nat, +n: Nat, +k: Nat, +m: Nat, r: TA.MMulTN<n, k, m>) -> IO(Unit):
  match left r:
    case Zero{} TA.MMulTN{a, b, c}: TT.show_c(n, m, c)
    case Succ{q} TA.MMulTN{a, b, c}: tn_go(q, par, n, k, m, tn_step(par, n, k, m, a, b, c))

def nn_step(+par: Nat, +n: Nat, +k: Nat, +m: Nat, a: TA.Mat<n, k>, b: TA.Mat<k, m>, c: TA.Mat<n, m>) -> TA.MMul<n, k, m>:
  TA.Mat.matmul_acc(n, k, m, par, a, b, c)

def nn_go(left: Nat, +par: Nat, +n: Nat, +k: Nat, +m: Nat, r: TA.MMul<n, k, m>) -> IO(Unit):
  match left r:
    case Zero{} TA.MMul{a, b, c}: TT.show_c(n, m, c)
    case Succ{q} TA.MMul{a, b, c}: nn_go(q, par, n, k, m, nn_step(par, n, k, m, a, b, c))

def run(+reps: Nat, +par: Nat) -> IO(Unit):
  do IO<Unit>:
    nt_go(reps, par, 256n, 576n, 1536n, TA.MMulNT{TT.rmat(256n, 576n, 1), TT.rmat(1536n, 576n, 2), TA.Mat.zeros(256n, 1536n)})
    tn_go(reps, par, 1536n, 256n, 576n, TA.MMulTN{TT.rmat(256n, 1536n, 3), TT.rmat(256n, 576n, 4), TA.Mat.zeros(1536n, 576n)})
    nn_go(reps, par, 256n, 1536n, 576n, TA.MMul{TT.rmat(256n, 1536n, 5), TT.rmat(1536n, 576n, 6), TA.Mat.zeros(256n, 576n)})
