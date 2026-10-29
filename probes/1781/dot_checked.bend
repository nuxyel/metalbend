import Base

type R is Type:
  R{a: Array<F32>, b: Array<F32>, s: F32}

def dot(k: Nat, +i: U32, a0: F32, a1: F32, a2: F32, a3: F32, ra: Array<F32> & F32, rb: Array<F32> & F32) -> R:
  match k ra rb:
    case 0n Tuple{a, x} Tuple{b, y}: R{a, b, ((a0 + a1 : F32) + (a2 + a3 : F32) : F32)}
    case 1n+p Tuple{a, +x} Tuple{b, +y}: dot(p, (i + 1 : U32), a1, a2, a3, (a0 + (x * y : F32) : F32), Array.get(F32, a, (i + 1 : U32)), Array.get(F32, b, (i + 1 : U32)))

def go(left: Nat, +acc: F32, r: R) -> F32:
  match left r:
    case 0n _: acc
    case 1n+q R{a, b, +s}: go(q, (acc + s : F32), dot(65536n, 0, 0.0, 0.0, 0.0, 0.0, Array.get(F32, a, 0), Array.get(F32, b, 0)))

def fill(left: Nat, +i: U32, +m: U32, a: Array<F32>) -> Array<F32>:
  match left:
    case 0n: a
    case 1n+q: fill(q, (i + 1 : U32), m, Array.set(F32, a, i, ((F32.from_nat(U32.to_nat(((i * m : U32) % 1000 : U32))) / 1000.0 : F32) - 0.5 : F32)))

def show(x: F32) -> IO(Unit):
  match x:
    case F32{w}: IO.print(U32.show(U32{w}))

def main() -> IO(Unit):
  show(go(4096n, 0.0, R{fill(65536n, 0, 7, Array.new(F32, 16n, 0.0)), fill(65536n, 0, 13, Array.new(F32, 16n, 0.0)), 0.0}))
