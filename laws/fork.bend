# A model of tensor-fork's split of a product into blocks (rpar and cpar in bend-ml-tensor-fork 0.1.4.0, gemm-fork's
# path). A node of depth 1 + q gives its first Nat.div(cnt, 2n) rows (or columns) to the left block and the rest, from
# i0 + Nat.div(cnt, 2n) on, to the right one; depth 0 is one block. The real code runs the two blocks in parallel on
# two handles to the same arrays (Base's @unsafe Array.fork), which no law can import; this file states the split
# alone, in two forms:
#
# - tree: the indexes each block visits, in the order the blocks sit in the tree (rows for rpar, columns for cpar);
# - blocks: rpar's blocks run one after another, left then right, each leaf being tensor-array's own t8_rows (the
#   real code, imported), each block starting from the arrays the one before it left.
#
# The offsets are counted in Nat (tree) or as steps of + 1 on a U32 (blocks, adv), where tensor-fork computes
# i0 + U32.from_nat(Nat.div(cnt, 2n)) in U32: the same number for every row below 2^32, but that equality is not proved.
import Base
import bend-ml-tensor-array@0.1.16.0/main.bend as TA

# the indexes one block visits: i0, i0 + 1, ..., cnt of them (t8_rows' rows, t8_cols' columns)
def rows(cnt: Nat, +i0: Nat) -> List<&2, Nat>:
  match cnt:
    case 0n:
      Nil{}
    case 1n+p:
      i0 <> rows(p, 1n+i0)

# the indexes the blocks of a tree of depth d visit, left block first
def tree(+d: Nat, +i0: Nat, +cnt: Nat) -> List<&2, Nat>:
  match d:
    case 0n:
      rows(cnt, i0)
    case 1n+q:
      List.append(&2, Nat, tree(q, i0, Nat.div(cnt, 2n)), tree(q, Nat.add(i0, Nat.div(cnt, 2n)), Nat.sub(cnt, Nat.div(cnt, 2n))))

# i advanced by one, a times: the row t8_rows reaches after a rows from i
def adv(a: Nat, +i: U32) -> U32:
  match a:
    case 0n:
      i
    case 1n+p:
      adv(p, (i + 1 : U32))

# rpar's blocks run one after another: the left block's rows, then the right block's on what the left one left
def blocks(+ac: Bool, +d: Nat, +cnt: Nat, +m: Nat, +tk: Nat, +tku: U32, +rot: Nat, +i0: U32, +mu: U32, g: TA.TG) -> TA.TG:
  match d:
    case 0n:
      TA.t8_rows(ac, cnt, m, tk, tku, rot, i0, mu, g)
    case 1n+q:
      blocks(ac, q, Nat.sub(cnt, Nat.div(cnt, 2n)), m, tk, tku, rot, adv(Nat.div(cnt, 2n), i0), mu, blocks(ac, q, Nat.div(cnt, 2n), m, tk, tku, rot, i0, mu, g))
