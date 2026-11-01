# tensor-array 0.1.18.0 helpers for the workloads on that version (lib/ta.bend's, at 0.1.18.0): random matrices and
# the hash of a matrix.
import Base
import bend-ml-tensor-array@0.1.18.0/main.bend as TA
import ./mb.bend as MB

def rmat2(+n: Nat, +seed: U32, -r: Nat, -c: Nat, m: TA.Mat<r, c>) -> TA.Mat<r, c>:
  match m:
    case TA.Mat{d}: TA.Mat{MB.rand(n, seed, d)}

# an r x c matrix of seed's values
def rmat(+r: Nat, +c: Nat, +seed: U32) -> TA.Mat<r, c>:
  rmat2(Nat.mul(r, c), seed, r, c, TA.Mat.zeros(r, c))

def show_c(+n: Nat, +m: Nat, c: TA.Mat<n, m>) -> IO(Unit):
  match c:
    case TA.Mat{d}: MB.show_hash(MB.hash(Nat.mul(n, m), d))

