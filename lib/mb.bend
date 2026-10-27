# MetalBend's shared pieces: deterministic inputs and the output hash every workload prints (its oracle).
import Base

def f2u(x: F32) -> U32:
  match x:
    case F32{w}: U32{w}

def u2f(u: U32) -> F32:
  match u:
    case U32{w}: F32{w}

# the value of cell i under a seed: a multiplicative hash of i, its top 23 bits as the mantissa of a number in [1, 2),
# shifted to [-0.5, 0.5); the same bits on every machine and every Bend version
def val(+seed: U32, +i: U32) -> F32:
  +h = (((i + seed : U32) * 2654435761 : U32) .^. (i >> 13n : U32) : U32)
  +g = ((h * 2246822519 : U32) .^. (h >> 16n) : U32)
  ((u2f(((g >> 9n) .|. 1065353216 : U32)) - 1.5) : F32)

def rand_go(left: Nat, +seed: U32, +i: U32, a: Array<F32>) -> Array<F32>:
  match left:
    case Zero{}: a
    case Succ{q}: rand_go(q, seed, (i + 1 : U32), Array.set(F32, a, i, val(seed, i)))

# fills the first n cells of a with seed's values
def rand(+n: Nat, +seed: U32, a: Array<F32>) -> Array<F32>:
  rand_go(n, seed, 0, a)

def rand_s_go(left: Nat, +seed: U32, +s: F32, +i: U32, a: Array<F32>) -> Array<F32>:
  match left:
    case Zero{}: a
    case Succ{q}: rand_s_go(q, seed, s, (i + 1 : U32), Array.set(F32, a, i, (val(seed, i) * s : F32)))

# the same values times s: weights scaled so a product keeps its input's size (s = 3.464 / sqrt(columns))
def rand_s(+n: Nat, +seed: U32, +s: F32, a: Array<F32>) -> Array<F32>:
  rand_s_go(n, seed, s, 0, a)

# FNV-1a over the bits of the first n cells: one changed bit in any cell changes the hash
def hash_go(left: Nat, +i: U32, +h: U32, r: Array<F32> & F32) -> Array<F32> & U32:
  match left r:
    case Zero{} Tuple{a, x}: (a, h)
    case Succ{q} Tuple{a, x}: hash_go(q, (i + 1 : U32), ((h .^. f2u(x)) * 16777619 : U32), Array.get(F32, a, i))

def hash(+n: Nat, a: Array<F32>) -> Array<F32> & U32:
  hash_go(n, 1, 2166136261, Array.get(F32, a, 0))

def show_hash(r: Array<F32> & U32) -> IO(Unit):
  match r:
    case Tuple{a, h}: IO.print(U32.show(h))
