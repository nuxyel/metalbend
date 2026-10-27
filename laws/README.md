# Laws

`LAWS.bend` states the claims, `PROOF.bend` proves them (plain Bend: no `@unsafe`, no `?TODO`, no axioms), and
`check.sh` is the gate: the proofs must check, with `--verdict` too, and every mutant of the model must break them.

- **t8_is_dotr**: on lines that are a whole number of cells of 8, tensor-array's Tile8 dot (sum q gets product q,
  then product q + 4, of each cell) and its scalar dot `dotr` (each product added to the first of four sums, which
  then rotate) build the same expression from the same starting sums. The numbers are expression trees (`E`: `Lit`,
  `Add`, `Mul`) and nothing is assumed about `Add` or `Mul`, so the two loops do the same operations in the same order
  and agree under any arithmetic, F32 bit for bit included. The proof is an induction on the cells: dotr's eight
  rotating steps over one cell compute, by evaluation alone, exactly Tile8's one step.
  - It is a law about a model of the two loops on lists of cells (`t8_dotr.bend`), not about tensor-array's `Array`
    code, which reads F32 cells the checker cannot see into; the model's lines are both made of whole cells (every
    product shape in the corpus: k = 256, 576, 1536).
  - Four mutants of the model are rejected (`check.sh`): a lane adding its two products in the other order, two lanes
    swapping a product, the sums combined in another pairing, and the first pair added as `s1 + s0`. The last is
    harmless in F32 (addition commutes), so no numeric test can see it: the law is stricter than "the same bits",
    because it assumes nothing about `Add`.
