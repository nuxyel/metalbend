# The cells of a product, as a list. tensor-array's Tile8 product (gemm-tile8's path, and gemm-fork's leaves) writes C
# in place, cell by cell, into an Array, which has no length to count; this file lists the writes instead. A W is one
# write: the row i and column j of C whose dot it computes, and the index cidx of C it goes to. cols and cells list them
# with the code's own arithmetic (U32 steps of + 1, the row's first index i * mu), and run does them in order, each
# with tensor-array's own cell (t8_cell) and write (t8_set), exactly as t8_cols does one. So the list is the model and
# every write in it is the real code.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA

# one write: the cell at row i, column j, into C at cidx
type W is Data:
  W{i: U32, j: U32, cidx: U32}

# the writes of m columns of row i, from column j and index cidx (t8_cols)
def cols(m: Nat, +i: U32, +j: U32, +cidx: U32) -> List<&2, W>:
  match m:
    case 0n:
      Nil{}
    case 1n+p:
      W{i, j, cidx} <> cols(p, i, (j + 1 : U32), (cidx + 1 : U32))

# the writes of n rows of m columns from row i, row i's first at i * mu (t8_rows)
def cells(n: Nat, +m: Nat, +i: U32, +mu: U32) -> List<&2, W>:
  match n:
    case 0n:
      Nil{}
    case 1n+p:
      List.append(&2, W, cols(m, i, 0, (i * mu : U32)), cells(p, m, (i + 1 : U32), mu))

# one write, as t8_cols does it: tensor-array's dot of row i of A and column j of B, written into C at cidx
def put(+ac: Bool, +tk: Nat, +tku: U32, +rot: Nat, w: W, g: TA.TG) -> TA.TG:
  match w g:
    case W{+i, +j, +cidx} TA.TG{a, b, c}:
      TA.t8_set(ac, cidx, c, TA.t8_cell(tk, tku, rot, i, j, a, b))

# the writes of ws, in order, each on what the one before left
def run(+ac: Bool, +tk: Nat, +tku: U32, +rot: Nat, ws: List<&2, W>, g: TA.TG) -> TA.TG:
  match ws:
    case Nil{}:
      g
    case Con{w, t}:
      run(ac, tk, tku, rot, t, put(ac, tk, tku, rot, w, g))

# t8_out_seq with the writes of cells in place of t8_rows: n rows of m columns from row 0, row i's first at i * m
def fin(+ac: Bool, +n: Nat, +m: Nat, +tk: Nat, +tku: U32, +rot: Nat, c: Array<F32>, p: TA.PKK) -> TA.G:
  match p:
    case TA.PKK{a, b, ta, tb}:
      TA.t8_g(a, b, run(ac, tk, tku, rot, cells(n, m, 0, U32.from_nat(m)), TA.TG{ta, tb, c}))

# tensor-array's sequential Tile8 product (gemm_t8_ac at depth 0): A and B packed by tensor-array's own pk_pack, in
# cells of 8 (ceil(k / 8) a line), then the writes of cells
def gemm(+ac: Bool, +n: Nat, +m: Nat, +k: Nat, +arow: U32, +sa: U32, +sb: U32, +bcol: U32, a: Array<F32>, b: Array<F32>, c: Array<F32>) -> TA.G:
  fin(ac, n, m, Nat.div(Nat.add(k, 7n), 8n), U32.from_nat(Nat.div(Nat.add(k, 7n), 8n)), Nat.mod(k, 4n), c, TA.t8_pk2(TA.pk_pack(n, Nat.div(Nat.add(k, 7n), 8n), k, arow, sa, a), TA.pk_pack(m, Nat.div(Nat.add(k, 7n), 8n), k, bcol, sb, b)))
