# MetalBend's laws. Each is a claim about every input; PROOF.bend proves them.
import Base
import ./t8_dotr.bend as D

# LAW (t8_is_dotr): on lines that are a whole number of Tile8 cells, the Tile8 dot and the scalar dot build the same
# expression from the same starting sums, so they agree under any arithmetic: F32, bit for bit, included.
law t8_is_dotr:
  for xs: List<D.C8>
  for ys: List<D.C8>
  for +s0: D.E
  for +s1: D.E
  for +s2: D.E
  for +s3: D.E
  {D.t8(xs, ys, s0, s1, s2, s3) == D.dotr(D.flat(xs), D.flat(ys), s0, s1, s2, s3) : D.E}
