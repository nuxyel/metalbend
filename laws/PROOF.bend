# The proofs of LAWS.bend: plain Bend, no @unsafe, no ?TODO, no axioms.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA
import ./t8_dotr.bend as D
import ./fork.bend as F
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

# ---- bands_len and matvec_l_len ----
#
# bend-ml proves the two pieces of this count (band_len: one band gives its rows; join_len: joining two halves adds
# their counts) but not the whole tree: the straight proof hands each band to the product and again to the induction
# hypothesis about it, and a band holds an Array, which can be used once. The way around it here: every step returns
# its result together with two proofs, "this is what the real code computes" and "it has this many numbers", in one
# record (AS, BS). The record is built once, by running the step; the proofs mention the real code only in their
# types, where nothing is used up.

def al_len(al: TA.AL) -> Nat:
  match al:
    case TA.AL{c, l}:
      List.length(&2, F32, l)

# a result al of read_l, the proof that read_l gives al, and the proof that al holds n numbers
type AS<-t: TA.AL, -n: Nat> is Type:
  AS{al: TA.AL, e: {al == t : TA.AL}, k: {al_len(al) == n : Nat}}

# the same for a band's product (a BL)
type BS<-r: Nat, -c: Nat, -t: TA.BL<r, c>, -n: Nat> is Type:
  BS{bl: TA.BL<r, c>, e: {bl == t : TA.BL<r, c>}, k: {TA.bl_len(r, c, bl) == n : Nat}}

# a record about t gives the count of t itself
def bs_out(-r: Nat, -c: Nat, -t: TA.BL<r, c>, -n: Nat, s: BS<r, c, t, n>) -> {TA.bl_len(r, c, t) == n : Nat}:
  match s:
    case BS{bl, e, k}:
      %e : {TA.bl_len(r, c, _) == n : Nat}
      k

def rl_step(+p: Nat, +l: Nat, -t: TA.AL, s: AS<t, Nat.add(1n+p, 1n+l)>) -> AS<t, 2n+Nat.add(p, l)>:
  match s:
    case AS{al, e, k}:
      AS{al, e, TA.len_step(al_len(al), p, l, k)}

# read_l reads mleft + 1 numbers onto acc (the induction of bend-ml's leaf_len, keeping the result)
def rl_c(+mleft: Nat, +idx: U32, +acc: List<&2, F32>, rc: Array<F32> & F32) -> AS<TA.read_l(mleft, idx, acc, rc), Nat.add(1n+mleft, List.length(&2, F32, acc))>:
  match mleft rc:
    case 0n Tuple{c, +v}:
      AS{TA.AL{c, List.reverse(&2, F32, v <> acc)}, {==}, TA.zero_out(List.length(&2, F32, List.reverse.go(&2, F32, v <> acc, Nil{})), 1n+List.length(&2, F32, acc), TA.rev_len(v <> acc, Nil{}))}
    case 1n+p Tuple{c, +v}:
      rl_step(p, List.length(&2, F32, acc), TA.read_l(p, (idx + 1 : U32), v <> acc, Array.get(F32, c, (idx + 1 : U32))), rl_c(p, (idx + 1 : U32), v <> acc, Array.get(F32, c, (idx + 1 : U32))))

def g2_eq(-r: Nat, -c: Nat, -w: Array<F32>, -d: Array<F32>, +l: List<&2, F32>, -t: TA.AL, e: {TA.AL{d, l} == t : TA.AL}) -> {TA.BL{TA.BLeaf{TA.Mat{w}}, l} == TA.bv_g2(r, c, w, t) : TA.BL<r, c>}:
  %e : {TA.BL{TA.BLeaf{TA.Mat{w}}, l} == TA.bv_g2(r, c, w, _) : TA.BL<r, c>}
  {==}

def g2_c(-r: Nat, -c: Nat, w: Array<F32>, -n: Nat, -t: TA.AL, s: AS<t, n>) -> BS<r, c, TA.bv_g2(r, c, w, t), n>:
  match s:
    case AS{al, e, k}:
      match al:
        case TA.AL{d, +l}:
          BS{TA.BL{TA.BLeaf{TA.Mat{w}}, l}, g2_eq(r, c, w, d, l, t, e), k}

def bs_zero(-r: Nat, -c: Nat, -t: TA.BL<r, c>, +n: Nat, s: BS<r, c, t, Nat.add(n, 0n)>) -> BS<r, c, t, n>:
  match s:
    case BS{bl, e, k}:
      BS{bl, e, TA.zero_out(TA.bl_len(r, c, bl), n, k)}

# a band of 1 + p rows: whatever the gemm wrote, reading it back gives 1 + p numbers
def g_c(-r: Nat, -c: Nat, +p: Nat, g: TA.G) -> BS<r, c, TA.bv_g(r, c, p, g), 1n+p>:
  match g:
    case TA.G{a, b, y}:
      bs_zero(r, c, TA.bv_g(r, c, p, TA.G{a, b, y}), 1n+p, g2_c(r, c, b, Nat.add(1n+p, 0n), TA.read_l(p, 0, Nil{}, Array.get(F32, y, 0)), rl_c(p, 0, Nil{}, Array.get(F32, y, 0))))

# one band (bend-ml's band_len, keeping the result)
def gemm_c(-r: Nat, +c: Nat, +rows: Nat, x: Array<F32>, w: Array<F32>) -> BS<r, c, TA.bv_gemm(r, c, rows, rows, x, w), rows>:
  match rows:
    case 0n:
      BS{TA.BL{TA.BLeaf{TA.Mat{w}}, Nil{}}, {==}, {==}}
    case 1n+p:
      g_c(r, c, p, TA.gemm(1n, 1n+p, c, U32.from_nat(c), 1, 1, U32.from_nat(c), x, w, Array.new(F32, TA.cap_depth(1n+p), 0.0)))

def mat_c(-r: Nat, +c: Nat, +rr: Nat, x: Array<F32>, m: TA.Mat<r, c>) -> BS<r, c, TA.bv_mat(r, c, rr, x, m), rr>:
  match m:
    case TA.Mat{w}:
      gemm_c(r, c, rr, x, w)

# half(rr) numbers and rr - half(rr) numbers make rr numbers (bend-ml's half_cover)
def join_k(+rr: Nat, +yx: List<&2, F32>, +yy: List<&2, F32>, kp: {List.length(&2, F32, yx) == TA.half(rr) : Nat}, kq: {List.length(&2, F32, yy) == Nat.sub(rr, TA.half(rr)) : Nat}) -> {List.length(&2, F32, List.append(&2, F32, yx, yy)) == rr : Nat}:
  %Equal.sym(Nat, rr, Nat.add(TA.half(rr), Nat.sub(rr, TA.half(rr))), TA.half_cover(rr)) : {List.length(&2, F32, List.append(&2, F32, yx, yy)) == _ : Nat}
  %kp : {List.length(&2, F32, List.append(&2, F32, yx, yy)) == Nat.add(_, Nat.sub(rr, TA.half(rr))) : Nat}
  %kq : {List.length(&2, F32, List.append(&2, F32, yx, yy)) == Nat.add(List.length(&2, F32, yx), _) : Nat}
  TA.app_len(yx, yy)

def join_e(-r: Nat, -c: Nat, -bx: TA.Bands<TA.half(r), c>, -by: TA.Bands<Nat.sub(r, TA.half(r)), c>, -yx: List<&2, F32>, -yy: List<&2, F32>, -P: TA.BL<TA.half(r), c>, -Q: TA.BL<Nat.sub(r, TA.half(r)), c>, ep: {TA.BL{bx, yx} == P : TA.BL<TA.half(r), c>}, eq: {TA.BL{by, yy} == Q : TA.BL<Nat.sub(r, TA.half(r)), c>}) -> {TA.BL{TA.BNode{bx, by}, List.append(&2, F32, yx, yy)} == TA.bv_join(r, c, P, Q) : TA.BL<r, c>}:
  %ep : {TA.BL{TA.BNode{bx, by}, List.append(&2, F32, yx, yy)} == TA.bv_join(r, c, _, Q) : TA.BL<r, c>}
  %eq : {TA.BL{TA.BNode{bx, by}, List.append(&2, F32, yx, yy)} == TA.bv_join(r, c, TA.BL{bx, yx}, _) : TA.BL<r, c>}
  {==}

# a node: the two halves' records give the node's (bend-ml's join_len, keeping the result)
def join_c(-r: Nat, -c: Nat, +rr: Nat, -P: TA.BL<TA.half(r), c>, -Q: TA.BL<Nat.sub(r, TA.half(r)), c>, sp: BS<TA.half(r), c, P, TA.half(rr)>, sq: BS<Nat.sub(r, TA.half(r)), c, Q, Nat.sub(rr, TA.half(rr))>) -> BS<r, c, TA.bv_join(r, c, P, Q), rr>:
  match sp sq:
    case BS{TA.BL{bx, +yx}, ep, kp} BS{TA.BL{by, +yy}, eq, kq}:
      BS{TA.BL{TA.BNode{bx, by}, List.append(&2, F32, yx, yy)}, join_e(r, c, bx, by, yx, yy, P, Q, ep, eq), join_k(rr, yx, yy, kp, kq)}

# induction on the bands, following bmv: a leaf is one band, a node joins its two halves
def bmv_c(+c: Nat, -r: Nat, b: TA.Bands<r, c>, +rr: Nat, -e: {rr == r : Nat}, xp: Array<F32> & Array<F32>) -> BS<r, c, TA.bmv(c, r, b, rr, e, xp), rr>:
  match b xp:
    case TA.BLeaf{m} Tuple{x, x2}:
      mat_c(r, c, rr, x, m)
    case TA.BNode{bx, by} Tuple{x1, x2}:
      join_c(r, c, rr, TA.bmv(c, TA.half(r), bx, TA.half(rr), TA.eq_half(rr, r, e), Array.clone(F32, x1)), TA.bmv(c, Nat.sub(r, TA.half(r)), by, Nat.sub(rr, TA.half(rr)), TA.eq_rest(rr, r, e), Array.clone(F32, x2)), bmv_c(c, TA.half(r), bx, TA.half(rr), TA.eq_half(rr, r, e), Array.clone(F32, x1)), bmv_c(c, Nat.sub(r, TA.half(r)), by, Nat.sub(rr, TA.half(rr)), TA.eq_rest(rr, r, e), Array.clone(F32, x2)))

def Laws.bands_len(c, r, b, rr, e, xp):
  bs_out(r, c, TA.bmv(c, r, b, rr, e, xp), rr, bmv_c(c, r, b, rr, e, xp))

# Bands.matvec_l is bmv on a copy of x, with rr = r
def Laws.matvec_l_len(r, c, b, x):
  Laws.bands_len(c, r, b, r, {==}, Array.clone(F32, TA.fill_list(x, 0, Array.new(F32, TA.cap_depth(c), 0.0))))

# ---- fork_cover, t8_rows_split and t8_blocks ----

# fst(divmod.go(n, m, d, r)) <= d + n: Base's division loop never counts past the steps it takes
def go_le(+n: Nat, +m: Nat, +d: Nat, +r: Nat) -> {True{} == TA.leb(Pair.fst(Nat, Nat, Nat.divmod.go(n, m, d, r)), Nat.add(d, n)) : Bool}:
  match n m:
    case 0n _:
      %Equal.sym(Nat, Nat.add(d, 0n), d, TA.add_zero_r(d)) : {True{} == TA.leb(d, _) : Bool}
      TA.leb_refl(d)
    case 1n+np 0n:
      %TA.add_succ_r(d, np) : {True{} == TA.leb(Pair.fst(Nat, Nat, Nat.divmod.go(np, r, 1n+d, 0n)), _) : Bool}
      go_le(np, r, 1n+d, 0n)
    case 1n+np 1n+mp:
      %TA.add_succ_r(d, np) : {True{} == TA.leb(Pair.fst(Nat, Nat, Nat.divmod.go(np, mp, d, 1n+r)), _) : Bool}
      TA.leb_succ(Pair.fst(Nat, Nat, Nat.divmod.go(np, mp, d, 1n+r)), Nat.add(d, np), go_le(np, mp, d, 1n+r))

# cnt / 2 <= cnt: the left block never takes more than there is
def div2_le(+cnt: Nat) -> {True{} == TA.leb(Nat.div(cnt, 2n), cnt) : Bool}:
  go_le(cnt, 1n, 0n, 0n)

# a + b indexes from i0 are a indexes from i0, then b from i0 + a
def rows_app(+a: Nat, +b: Nat, +i0: Nat) -> {F.rows(Nat.add(a, b), i0) == List.append(&2, Nat, F.rows(a, i0), F.rows(b, Nat.add(i0, a))) : List<&2, Nat>}:
  match a:
    case 0n:
      %Equal.sym(Nat, Nat.add(i0, 0n), i0, TA.add_zero_r(i0)) : {F.rows(b, i0) == F.rows(b, _) : List<&2, Nat>}
      {==}
    case 1n+p:
      %TA.add_succ_r(i0, p) : {F.rows(1n+Nat.add(p, b), i0) == List.append(&2, Nat, F.rows(1n+p, i0), F.rows(b, _)) : List<&2, Nat>}
      %Equal.sym(List<&2, Nat>, F.rows(Nat.add(p, b), 1n+i0), List.append(&2, Nat, F.rows(p, 1n+i0), F.rows(b, Nat.add(1n+i0, p))), rows_app(p, b, 1n+i0)) : {i0 <> _ == i0 <> List.append(&2, Nat, F.rows(p, 1n+i0), F.rows(b, 1n+Nat.add(i0, p))) : List<&2, Nat>}
      {==}

# Induction on the depth. Each block of the node is, by the law one level down, a plain run over its indexes; the two
# runs are one run over cnt / 2 + (cnt - cnt / 2) indexes (rows_app), and that is cnt (bend-ml's add_sub, with
# div2_le).
def Laws.fork_cover(d, i0, cnt):
  match d:
    case 0n:
      {==}
    case 1n+q:
      %Equal.sym(List<&2, Nat>, F.tree(q, i0, Nat.div(cnt, 2n)), F.rows(Nat.div(cnt, 2n), i0), Laws.fork_cover(q, i0, Nat.div(cnt, 2n))) : {List.append(&2, Nat, _, F.tree(q, Nat.add(i0, Nat.div(cnt, 2n)), Nat.sub(cnt, Nat.div(cnt, 2n)))) == F.rows(cnt, i0) : List<&2, Nat>}
      %Equal.sym(List<&2, Nat>, F.tree(q, Nat.add(i0, Nat.div(cnt, 2n)), Nat.sub(cnt, Nat.div(cnt, 2n))), F.rows(Nat.sub(cnt, Nat.div(cnt, 2n)), Nat.add(i0, Nat.div(cnt, 2n))), Laws.fork_cover(q, Nat.add(i0, Nat.div(cnt, 2n)), Nat.sub(cnt, Nat.div(cnt, 2n)))) : {List.append(&2, Nat, F.rows(Nat.div(cnt, 2n), i0), _) == F.rows(cnt, i0) : List<&2, Nat>}
      %Equal.sym(Nat, cnt, Nat.add(Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n))), TA.add_sub(Nat.div(cnt, 2n), cnt, div2_le(cnt))) : {List.append(&2, Nat, F.rows(Nat.div(cnt, 2n), i0), F.rows(Nat.sub(cnt, Nat.div(cnt, 2n)), Nat.add(i0, Nat.div(cnt, 2n)))) == F.rows(_, i0) : List<&2, Nat>}
      Equal.sym(List<&2, Nat>, F.rows(Nat.add(Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n))), i0), List.append(&2, Nat, F.rows(Nat.div(cnt, 2n), i0), F.rows(Nat.sub(cnt, Nat.div(cnt, 2n)), Nat.add(i0, Nat.div(cnt, 2n)))), rows_app(Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n)), i0))

# Induction on a. No row left: both sides are the second loop. One row: both sides do row i (t8_cols) first, then the
# law one row shorter from row i + 1. The arrays (g) appear only in the statement, never used up.
def Laws.t8_rows_split(ac, a, b, m, tk, tku, rot, i, mu, g):
  match a:
    case 0n:
      {==}
    case 1n+p:
      Laws.t8_rows_split(ac, p, b, m, tk, tku, rot, (i + 1 : U32), mu, TA.t8_cols(ac, m, tk, tku, rot, i, 0, (i * mu : U32), g))

# Induction on the depth, as fork_cover: each block is a plain t8_rows by the law one level down, and the two runs are
# one run over all cnt rows by t8_rows_split.
def Laws.t8_blocks(ac, d, cnt, m, tk, tku, rot, i0, mu, g):
  match d:
    case 0n:
      {==}
    case 1n+q:
      %Equal.sym(TA.TG, F.blocks(ac, q, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g), TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g), Laws.t8_blocks(ac, q, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g)) : {F.blocks(ac, q, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, _) == TA.t8_rows(ac, cnt, m, tk, tku, rot, i0, mu, g) : TA.TG}
      %Equal.sym(TA.TG, F.blocks(ac, q, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g)), TA.t8_rows(ac, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g)), Laws.t8_blocks(ac, q, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g))) : {_ == TA.t8_rows(ac, cnt, m, tk, tku, rot, i0, mu, g) : TA.TG}
      %Equal.sym(Nat, cnt, Nat.add(Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n))), TA.add_sub(Nat.div(cnt, 2n), cnt, div2_le(cnt))) : {TA.t8_rows(ac, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g)) == TA.t8_rows(ac, _, m, tk, tku, rot, i0, mu, g) : TA.TG}
      Equal.sym(TA.TG, TA.t8_rows(ac, Nat.add(Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n))), m, tk, tku, rot, i0, mu, g), TA.t8_rows(ac, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, F.adv(Nat.div(cnt, 2n), i0), mu, TA.t8_rows(ac, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g)), Laws.t8_rows_split(ac, Nat.div(cnt, 2n), Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, i0, mu, g))
