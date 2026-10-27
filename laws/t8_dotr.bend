# A law about tensor-array's two dot products: the Tile8 loop (cells of 8, sum q gets products q and q+4 of each cell)
# builds the very same expression as the scalar loop dotr (each product added to the first of four sums, which then
# rotate), so the two give the same result under any arithmetic, F32 bit for bit included.
#
# The numbers are expression trees (E): a sum is Add{a, b}, a product Mul{a, b}. Nothing is assumed about Add or Mul
# (not even that they commute), so the law says the two loops do the same operations in the same order, which is
# what "the same bits" needs. It is stated over a model of the loops on lists of cells, not over tensor-array's
# Array code, which reads F32 cells from arrays the checker cannot see into.
import Base

type E is Data:
  Lit{n: Nat}
  Add{a: E, b: E}
  Mul{a: E, b: E}

# eight numbers: one Tile8 cell
type C8 is Data:
  C8{x0: E, x1: E, x2: E, x3: E, x4: E, x5: E, x6: E, x7: E}

def fin(+a0: E, +a1: E, +a2: E, +a3: E) -> E:
  Add{Add{a0, a1}, Add{a2, a3}}

# dotr: product p is added to a0, then the sums rotate (a1, a2, a3, a0 + p); it stops at the shorter list
def dotr(xs: List<E>, ys: List<E>, +a0: E, +a1: E, +a2: E, +a3: E) -> E:
  match xs ys:
    case Con{x, xt} Con{y, yt}: dotr(xt, yt, a1, a2, a3, Add{a0, Mul{x, y}})
    case _ _: fin(a0, a1, a2, a3)

# t8_dot: per cell, sum q gets product q, then product q + 4; a whole number of cells, so the sums end unrotated
def t8(xs: List<C8>, ys: List<C8>, +s0: E, +s1: E, +s2: E, +s3: E) -> E:
  match xs ys:
    case Con{C8{x0, x1, x2, x3, x4, x5, x6, x7}, xt} Con{C8{y0, y1, y2, y3, y4, y5, y6, y7}, yt}:
      t8(xt, yt, Add{Add{s0, Mul{x0, y0}}, Mul{x4, y4}}, Add{Add{s1, Mul{x1, y1}}, Mul{x5, y5}}, Add{Add{s2, Mul{x2, y2}}, Mul{x6, y6}}, Add{Add{s3, Mul{x3, y3}}, Mul{x7, y7}})
    case _ _: fin(s0, s1, s2, s3)

# the cells' numbers in order: what Tile8's packing reads from a line
def flat(xs: List<C8>) -> List<E>:
  match xs:
    case Nil{}: Nil{}
    case Con{C8{x0, x1, x2, x3, x4, x5, x6, x7}, t}: x0 <> x1 <> x2 <> x3 <> x4 <> x5 <> x6 <> x7 <> flat(t)
