# MetalBend's laws. Each is a claim about every input; PROOF.bend proves them.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
import ./t8_dotr.bend as D
import ./fork.bend as F
import ./cells.bend as C

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

# LAW (fork_cover): tensor-fork's split, at any depth, visits the indexes i0 .. i0 + cnt - 1 each once and in order,
# as one block would. About a model of the split (fork.bend).
law fork_cover:
  for +d: Nat
  for +i0: Nat
  for +cnt: Nat
  {F.tree(d, i0, cnt) == F.rows(cnt, i0) : List<&2, Nat>}

# LAW (t8_rows_split): tensor-array's row loop over a + b rows is its loop over a rows followed by its loop over the
# next b rows. About the real code.
law t8_rows_split:
  for +ac: Bool
  for +a: Nat
  for +b: Nat
  for +m: Nat
  for +tk: Nat
  for +tku: U32
  for +rot: Nat
  for +i: U32
  for +mu: U32
  for -g: TA.TG
  {TA.t8_rows(ac, Nat.add(a, b), m, tk, tku, rot, i, mu, g) == TA.t8_rows(ac, b, m, tk, tku, rot, F.adv(a, i), mu, TA.t8_rows(ac, a, m, tk, tku, rot, i, mu, g)) : TA.TG}

# LAW (t8_blocks): tensor-fork's row blocks, run one after another, are tensor-array's sequential product: the same
# computation on the same arrays, so the same bits. The leaves are the real t8_rows; the tree is the model (fork.bend).
law t8_blocks:
  for +ac: Bool
  for +d: Nat
  for +cnt: Nat
  for +m: Nat
  for +tk: Nat
  for +tku: U32
  for +rot: Nat
  for +i0: U32
  for +mu: U32
  for -g: TA.TG
  {F.blocks(ac, d, cnt, m, tk, tku, rot, i0, mu, g) == TA.t8_rows(ac, cnt, m, tk, tku, rot, i0, mu, g) : TA.TG}

# LAW (t8_cols_cells): tensor-array's column loop over m columns of row i is the m writes of C.cols, one per column, in
# order, each the real cell write. About the real code; the list is the model (cells.bend).
law t8_cols_cells:
  for +ac: Bool
  for +m: Nat
  for +tk: Nat
  for +tku: U32
  for +rot: Nat
  for +i: U32
  for +j: U32
  for +cidx: U32
  for g: TA.TG
  {TA.t8_cols(ac, m, tk, tku, rot, i, j, cidx, g) == C.run(ac, tk, tku, rot, C.cols(m, i, j, cidx), g) : TA.TG}

# LAW (t8_rows_cells): tensor-array's row loop over n rows of m columns is the writes of C.cells, row by row. About the
# real code; the list is the model.
law t8_rows_cells:
  for +ac: Bool
  for +n: Nat
  for +m: Nat
  for +tk: Nat
  for +tku: U32
  for +rot: Nat
  for +i: U32
  for +mu: U32
  for g: TA.TG
  {TA.t8_rows(ac, n, m, tk, tku, rot, i, mu, g) == C.run(ac, tk, tku, rot, C.cells(n, m, i, mu), g) : TA.TG}

# LAW (cells_len): n rows of m columns are n x m writes.
law cells_len:
  for +n: Nat
  for +m: Nat
  for +i: U32
  for +mu: U32
  {List.length(&2, C.W, C.cells(n, m, i, mu)) == Nat.mul(n, m) : Nat}

# LAW (gemm_t8_cells): gemm-tile8's product (tensor-array's gemm_any at par 0, two rows or more, every form: A · B,
# A · Bt, At · B, into C or added to it) packs A and B and then does the writes of C.cells for its n rows of m
# columns: n x m cells of C, each once, row by row, by cells_len. About the real code from the entry point down.
law gemm_t8_cells:
  for +ac: Bool
  for +n: Nat
  for +m: Nat
  for +k: Nat
  for +arow: U32
  for +sa: U32
  for +sb: U32
  for +bcol: U32
  for a: Array<F32>
  for b: Array<F32>
  for c: Array<F32>
  {TA.gemm_any(ac, TA.split_depth(0n, 2n+n, m, k), 2n+n, m, k, arow, sa, sb, bcol, a, b, c) == C.gemm(ac, 2n+n, m, k, arow, sa, sb, bcol, a, b, c) : TA.G}
