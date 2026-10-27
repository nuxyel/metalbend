# The proofs of LAWS.bend: plain Bend, no @unsafe, no ?TODO, no axioms.
import Base
import ./t8_dotr.bend as D
import ./LAWS.bend as Laws

# Induction on the cells. One cell of each line: Tile8 takes it in one step; flat lays its eight numbers out, and dotr
# takes them in eight steps, which by computation leave the four sums exactly as Tile8's step does (sum q has gained
# product q, then product q + 4: the rotation brings each sum back to its place every four steps). Both then go on
# with the rest of the lines from the same sums, which is the law again, one cell shorter. When either line has no
# cell left, both stop and combine the same four sums.
def Laws.t8_is_dotr(xs, ys, s0, s1, s2, s3):
  match xs ys:
    case Con{D.C8{x0, x1, x2, x3, x4, x5, x6, x7}, xt} Con{D.C8{y0, y1, y2, y3, y4, y5, y6, y7}, yt}:
      Laws.t8_is_dotr(xt, yt, D.Add{D.Add{s0, D.Mul{x0, y0}}, D.Mul{x4, y4}}, D.Add{D.Add{s1, D.Mul{x1, y1}}, D.Mul{x5, y5}}, D.Add{D.Add{s2, D.Mul{x2, y2}}, D.Mul{x6, y6}}, D.Add{D.Add{s3, D.Mul{x3, y3}}, D.Mul{x7, y7}})
    case Nil{} _:
      {==}
    case Con{c, xt} Nil{}:
      {==}
