# Laws

`LAWS.bend` states the claims, `PROOF.bend` proves them (plain Bend: no `@unsafe`, no `?TODO`, no axioms), and
`check.sh` is the gate: the proofs must check, with `--verdict` too, and every mutant in `mutants.sh` must break them.
A mutant is one changed line in a scratch copy: a model, a statement, or tensor-array's own code (a copy of the
published 0.1.16.0 that must still check by itself, so the failure comes from these laws). `VERBOSE=1
laws/mutants.sh` shows where the checker stops on each.

Some laws speak about the real package code, imported at the version the workloads pin; others about a model of it,
written here, when the real code cannot be imported or read by the checker. Each one below says which.

## t8_is_dotr: the eight-wide dot product is the scalar one

On lines that are a whole number of cells of 8, tensor-array's Tile8 dot (sum q gets product q, then product q + 4,
of each cell) and its scalar dot `dotr` (each product added to the first of four sums, which then rotate) build the
same expression from the same starting sums. The numbers are expression trees (`E`: `Lit`, `Add`, `Mul`) and nothing
is assumed about `Add` or `Mul`, so the two loops do the same operations in the same order and agree under any
arithmetic, F32 bit for bit included. The proof is an induction on the cells: dotr's eight rotating steps over one
cell compute, by evaluation alone, exactly Tile8's one step.

- A model of the two loops on lists of cells (`t8_dotr.bend`), not tensor-array's `Array` code, which reads F32 cells
  the checker cannot see into; the model's lines are both made of whole cells (every product shape in the corpus:
  k = 256, 576, 1536).
- Four mutants: a lane adding its two products in the other order, two lanes swapping a product, the sums combined in
  another pairing, and the first pair added as `s1 + s0`. The last is harmless in F32 (addition commutes), so no
  numeric test can see it: the law is stricter than "the same bits", because it assumes nothing about `Add`.

## bands_len and matvec_l_len: matrix · vector over bands gives one number per row

matvec-bands multiplies a matrix cut into 16 bands of rows (tensor-array's `Bands`) by a vector. `bands_len` says that
the product (`bmv`, which `Bands.matvec` runs) gives exactly as many numbers as the matrix has rows, whatever the
bands; `matvec_l_len` says the same of the public `Bands.matvec_l`. So no row is skipped or done twice: the
2048 numbers the workload hashes (and the 8192 in between) are all products, none a zero left over in the output.

- Real code: tensor-array 0.1.16.0, imported. bend-ml proves the pieces (`band_len`: one band gives its rows;
  `join_len`: two halves add up; `half_cover`: the halves of r rows are r rows) and left the whole tree open, because
  the straight proof hands each band to the product and again to the induction step, and a band holds an `Array`,
  which can be used only once. The proof here goes around it: each step returns its result together with two proofs,
  "this is what the real code computes" and "it holds this many numbers", in one record, so each band is used once,
  and the proofs mention the real code only in their types, where nothing is used up.
- It counts; it does not say which product lands where. A mutant that puts the second band's numbers before the
  first's keeps the count (bend-ml's own `join_len` refuses that one).
- Three mutants: a band multiplying only the first half of its rows, a band reading back one number fewer than its
  rows (both in a copy of tensor-array that still checks by itself), and the statement claiming one number more.

## fork_cover: tensor-fork's blocks cover the rows once, in order

gemm-fork splits each product into up to 8 blocks: a node gives its first half (`cnt / 2` rows or columns) to the
left block and the rest, from `i0 + cnt / 2` on, to the right one. `fork_cover` says that at any depth the blocks,
read left to right, visit `i0, i0 + 1, ..., i0 + cnt - 1`: each index once, in the order one block would.

- A model of the split (`fork.bend`): tensor-fork's own code shares the arrays between the blocks with Base's
  `@unsafe` `Array.fork`, which a law cannot import. The model copies the split's arithmetic (`Nat.div`, `Nat.sub`)
  from it; it covers the row split (`rpar`) and the column split (`cpar`) alike.
- Four mutants: the right block starting one index late, the right block taking `cnt / 2` indexes too (an odd count
  loses its last), the right block listed first, and the statement claiming the indexes start at 0.

## t8_rows_split and t8_blocks: the blocks compute tensor-array's sequential product

`t8_rows_split` says that tensor-array's Tile8 row loop over `a + b` rows is the loop over `a` rows followed by the
loop over the next `b` rows, on what the first left. `t8_blocks` builds on it: tensor-fork's row blocks, run one after
another, left first, compute exactly what tensor-array's sequential loop computes over all the rows, on the same
arrays. That is why gemm-fork and gemm-tile8 print the same hashes, by proof rather than by test, for the products
that split by rows.

- `t8_rows_split` is about the real code (tensor-array's `t8_rows`). `t8_blocks` has the real `t8_rows` as its
  leaves and the model's tree around them. Three steps stay unproved: (1) the real blocks run in parallel on shared
  arrays, so "one after another" equals "in parallel" only because each block writes its own rows of C and only reads
  A and B, which tensor-fork does not check (its tests sample it); (2) tensor-fork computes the right block's first row
  as `i0 + cnt / 2` in U32, the model as `cnt / 2` steps of + 1, the same number below 2^32; (3) the packing into cells
  of 8, which tensor-fork also does in blocks.
- It covers the row split only: two of gemm-fork's three products (256 x 1536 and 256 x 576) have more columns than
  rows and split by columns, where the blocks write C in another order than the sequential loop. For those,
  `fork_cover` shows each column is done once, and the cells are the same `t8_cell`s, but the claim that the order of
  the writes does not matter is not proved.
- Five mutants: the row loop skipping every other row (in a copy of tensor-array that still checks by itself), the
  statement's second loop starting again at row `i`, the right block starting at the size of the right half (wrong
  when `cnt` is odd), the right block running `cnt / 2` rows, and the right block running first. The last one is
  harmless to the result, since the two blocks write different rows; the law refuses it because it states the same
  computation step by step, which is stricter than "the same arrays at the end".

## t8_cols_cells, t8_rows_cells, cells_len and gemm_t8_cells: the product writes every cell of C once

gemm-tile8's products write C in place, one cell at a time, into an `Array`, and an array has no length that could be
counted the way `bands_len` counts a list. So these laws count the writes instead. `cells.bend` lists them: a write is
a row i of A, a column j of B, and the index of C where their dot goes, and the list for n rows of m columns is row
0's m writes, then row 1's, and so on. Running a list does each write with tensor-array's own cell and write functions
(`t8_cell`, `t8_set`), in order.

- `t8_cols_cells` and `t8_rows_cells`: tensor-array's column loop and row loop are exactly the writes of that list,
  one after another: no cell skipped, none done twice, none out of order.
- `cells_len`: n rows of m columns are n x m writes.
- `gemm_t8_cells`: from the entry point gemm-tile8 calls (`gemm_any`, at par 0, with two rows or more, for all three
  of its products and the accumulating forms), the product packs A and B into cells of 8 and then does the writes of
  that list for its n rows and m columns. With `cells_len`, that is n x m cells of C, each (row, column) once.
- Real code: tensor-array 0.1.16.0, imported, from `gemm_any` down to each cell; the list of writes is the only
  model, and every write in it calls the real code. The proof uses the same trick as `bands_len` (a result carried with
  its two descriptions in one record), because the arrays can be used only once.
- What it does not say: that the index i x m + j of each write lands on a different cell of C. The code computes it in
  U32, which wraps at 2^32, and an `Array` index wraps at the array's size. Neither happens in the corpus (the largest
  C has 884,736 cells, and tensor-array proves that `cap_depth`, which sizes `Mat.zeros`, gives room for n x m), but
  these laws do not connect the indexes to the cells. It says nothing either about the values (that is `t8_is_dotr`), the packing into cells
  of 8, or the parallel path: gemm-fork's row blocks are `t8_rows` on part of the rows, which `t8_rows_cells` covers
  (any first row and any row length), and its column blocks run `t8_cols` from a column j0, which `t8_cols_cells`
  covers, but the tree that hands out the blocks over shared arrays stays out (`t8_blocks` has its limits). One-row
  products take the scalar loop, which these laws do not reach; no product in gemm-tile8 has one row.
- Six mutants: a row writing every other cell of C, each row writing one cell fewer than its columns, the sequential
  product starting at C's second row, two-row products leaving the Tile8 path (all four in a copy of tensor-array
  that still checks by itself), the list doing the first row n times, and the statement claiming one write more per
  row. The list mutant keeps the count at n x m, so `cells_len` alone would let it through; the law about the real
  code refuses it.
