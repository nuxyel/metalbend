# The cost of an array read in a scalar loop: tensor-array's dot (four sums that rotate, dotr) over two arrays of 2^16
# F32, 4096 times. Each Array.get compiles to a load at (index & mask), the mask unknown to clang, so the loop keeps
# an `and` per read and clang unrolls it by 2, which leaves a register copy for the rotation of 4. dot_mask.c is the
# same loop in C, with the same bits.
import Base
import ../lib/mb.bend as MB

type R is Type:
  R{a: Array<F32>, b: Array<F32>, s: F32}

def dot(k: Nat, +i: U32, a0: F32, a1: F32, a2: F32, a3: F32, ra: Array<F32> & F32, rb: Array<F32> & F32) -> R:
  match k ra rb:
    case 0n Tuple{a, x} Tuple{b, y}: R{a, b, ((a0 + a1 : F32) + (a2 + a3 : F32) : F32)}
    case 1n+p Tuple{a, +x} Tuple{b, +y}: dot(p, (i + 1 : U32), a1, a2, a3, (a0 + (x * y : F32) : F32), Array.get(F32, a, (i + 1 : U32)), Array.get(F32, b, (i + 1 : U32)))

# each round's dot reads the arrays again; acc collects the results, so no round can be skipped
def go(left: Nat, +acc: F32, r: R) -> F32:
  match left r:
    case 0n _: acc
    case 1n+q R{a, b, +s}: go(q, (acc + s : F32), dot(65536n, 0, 0.0, 0.0, 0.0, 0.0, Array.get(F32, a, 0), Array.get(F32, b, 0)))

def main() -> IO(Unit):
  IO.print(U32.show(MB.f2u(go(4096n, 0.0, R{MB.rand(65536n, 1, Array.new(F32, 16n, 0.0)), MB.rand(65536n, 2, Array.new(F32, 16n, 0.0)), 0.0}))))
