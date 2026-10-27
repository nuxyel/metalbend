# softmax-ce over an Array with tail loops instead of tensor-array's lists: the same operations in the same order, so the
# same output as workloads/softmax-ce; splits the cost of the lists from the compiler's.
import Base
import ../lib/mb.bend as MB

def label(+i: U32) -> Nat:
  U32.to_nat(((((i * 2654435761 : U32) >> 7n) : U32) % 49152 : U32))

def hit(b: Bool) -> F32:
  match b:
    case True{}: 1.0
    case False{}: 0.0

# the max of cells i.. (m holds the max so far)
def amax(left: Nat, +i: U32, +m: F32, r: Array<F32> & F32) -> Array<F32> & F32:
  match left r:
    case Zero{} Tuple{a, x}: (a, m)
    case Succ{q} Tuple{a, +x}: amax(q, (i + 1 : U32), F32.max(m, x), Array.get(F32, a, (i + 1 : U32)))

# cell i becomes exp(cell - m); s is the running sum of those
def aexp(left: Nat, +i: U32, +m: F32, +s: F32, r: Array<F32> & F32) -> Array<F32> & F32:
  match left r:
    case Zero{} Tuple{a, x}: (a, s)
    case Succ{q} Tuple{a, +x}:
      +e = F32.exp((x - m : F32))
      aexp(q, (i + 1 : U32), m, (s + e : F32), Array.get(F32, Array.set(F32, a, i, e), (i + 1 : U32)))

# cell i (column j) becomes the gradient (e / s - onehot) / 64; a[y] is read before by arow
def agrad(left: Nat, +i: U32, +j: Nat, +y: Nat, +s: F32, r: Array<F32> & F32) -> Array<F32>:
  match left r:
    case Zero{} Tuple{a, x}: a
    case Succ{q} Tuple{a, +x}: agrad(q, (i + 1 : U32), 1n+j, y, s, Array.get(F32, Array.set(F32, a, i, ((((x / s : F32) - hit(Nat.is_eq(j, y)) : F32) / 64.0) : F32)), (i + 1 : U32)))

def arow3(+o: U32, +y: Nat, +s: F32, +loss: F32, r: Array<F32> & F32) -> Array<F32> & F32:
  match r:
    case Tuple{a, +ey}: (agrad(49152n, o, 0n, y, s, Array.get(F32, a, o)), (loss - F32.log(F32.max((ey / s : F32), 0.000000000001)) : F32))

def arow2(+o: U32, +y: Nat, +loss: F32, r: Array<F32> & F32) -> Array<F32> & F32:
  match r:
    case Tuple{a, +s}: arow3(o, y, s, loss, Array.get(F32, a, (o + U32.from_nat(y) : U32)))

def arow1(+o: U32, +y: Nat, +loss: F32, r: Array<F32> & F32) -> Array<F32> & F32:
  match r:
    case Tuple{a, +m}: arow2(o, y, loss, aexp(49152n, o, m, 0.0, Array.get(F32, a, o)))

# the max of a row from its first cell, as tensor-array's maxl
def amax0(+o: U32, r: Array<F32> & F32) -> Array<F32> & F32:
  match r:
    case Tuple{a, +x0}: amax(49151n, (o + 1 : U32), x0, Array.get(F32, a, (o + 1 : U32)))

# rows i..: row i's label is that of index seed + 63 - i, as labels_go's prepending gives
def arows(left: Nat, +i: U32, +seed: U32, r: Array<F32> & F32) -> Array<F32> & F32:
  match left r:
    case Zero{} _: r
    case Succ{q} Tuple{a, +loss}: arows(q, (i + 1 : U32), seed, arow1((i * 49152 : U32), label(((seed + 63 : U32) - i : U32)), loss, amax0((i * 49152 : U32), Array.get(F32, a, (i * 49152 : U32)))))

# acc[t] = acc[t] - (-1 * g[t]), tensor-array's Mat.add
def aadd(left: Nat, +t: U32, ra: Array<F32> & F32, rg: Array<F32> & F32) -> Array<F32>:
  match left ra rg:
    case Zero{} Tuple{a, x} Tuple{g, y}: a
    case Succ{q} Tuple{a, +x} Tuple{g, +y}: aadd(q, (t + 1 : U32), Array.get(F32, Array.set(F32, a, t, (x - ((0.0 - 1.0 : F32) * y : F32) : F32)), (t + 1 : U32)), Array.get(F32, g, (t + 1 : U32)))

def round_fin(acc: Array<F32>, r: Array<F32> & F32) -> IO(Array<F32>):
  match r:
    case Tuple{g, +loss}:
      do IO<Array<F32>>:
        IO.print(U32.show(MB.f2u((loss / 64.0 : F32))))
        return aadd(3145728n, 0, Array.get(F32, acc, 0), Array.get(F32, g, 0))

def go(left: Nat, +seed: U32, acc: Array<F32>) -> IO(Unit):
  match left:
    case Zero{}: MB.show_hash(MB.hash(3145728n, acc))
    case Succ{q}:
      do IO<Unit>:
        acc2 : Array<F32> <- round_fin(acc, arows(64n, 0, seed, (MB.rand(3145728n, seed, Array.new(F32, 22n, 0.0)), 0.0)))
        go(q, (seed + 1 : U32), acc2)

def main() -> IO(Unit):
  go(6n, 7, Array.new(F32, 22n, 0.0))
