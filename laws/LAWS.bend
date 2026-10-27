# MetalBend's laws. Each is a claim about every input; PROOF.bend proves them.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
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

# LAW (bands_len): tensor-array's matrix · vector over bands (bmv, what Bands.matvec runs) gives exactly rr numbers
# for a matrix of rr rows, whatever the bands: every row's product is in the result once. About the real code.
law bands_len:
  for +c: Nat
  for -r: Nat
  for b: TA.Bands<r, c>
  for +rr: Nat
  for -e: {rr == r : Nat}
  for xp: Array<F32> & Array<F32>
  {TA.bl_len(r, c, TA.bmv(c, r, b, rr, e, xp)) == rr : Nat}

# LAW (matvec_l_len): the same for the public Bands.matvec_l: r rows in, r numbers out.
law matvec_l_len:
  for +r: Nat
  for +c: Nat
  for b: TA.Bands<r, c>
  for +x: List<&2, F32>
  {TA.bl_len(r, c, TA.Bands.matvec_l(r, c, b, x)) == r : Nat}
