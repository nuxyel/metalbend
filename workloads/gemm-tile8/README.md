# gemm-tile8

The three matrix products of one SmolLM2-135M feed-forward layer at a batch of 256 tokens, through tensor-array's
sequential product (its Tile8 loop: eight-wide dots, four partial sums). Each product is 226.5 M multiply-adds, and
each is repeated 8 times into the same C (the accumulating forms):

| Product | Shape | In training |
|---|---|---|
| `nt` | C(256 x 1536) += A(256 x 576) · B(1536 x 576)ᵀ | the forward product |
| `tn` | C(1536 x 576) += A(256 x 1536)ᵀ · B(256 x 576) | a weight gradient |
| `nn` | C(256 x 576) += A(256 x 1536) · B(1536 x 576) | an input gradient |

The inputs are `lib/mb.bend`'s deterministic values; the program reads no files.

## Where it comes from

`bend-ml-tensor-array@0.1.16.0` (bend-ml), the products every bend-ml, llama.bend and BendTorch layer calls, at
`par 0` (one block, no parallelism). The workload is `main.bend` calling `lib/gemm.bend`, which `gemm-fork` and the GPU
target share with their own back ends.

## The C target

`native.c`: the same three products, the same 8 repetitions, the same order of additions as tensor-array's Tile8 loop
(product p of a dot goes to partial sum p mod 4, the four sums joined as (s0 + s1) + (s2 + s3), each dot added once into
C). A plain loop nest, no blocking for the cache: the yardstick for the sequential product.

## The GPU target

`gpu.bend` runs the same products through `bend-ml-tensor-gpu@0.1.4.0` (`lib/gemm_gpu.bend`), one bang a product. It
prints the CPU's hashes on the GPU too: tensor-gpu keeps tensor-array's four partial sums, and Bend builds the device
code without fused multiply-add. Its `gemm-tile8:gpu` line in `oracles.tsv` is the CPU's hash.

## The oracle

It prints the hash of each C, in the order nt, tn, nn: `0c6d7fee9a7ddf37`, the same as `gemm-fork`'s.

## The mutants (`scripts/mutate.py`)

- the forward product's B from another seed (`lib/gemm.bend`): caught;
- C: a product's third partial sum takes the fourth cell: caught.

## The laws

`t8_is_dotr` (the eight-wide dot and the scalar dot build the same expression) and `t8_cols_cells`, `t8_rows_cells`,
`cells_len`, `gemm_t8_cells` (the product writes n x m cells of C, each once, row by row). `laws/README.md` has each
one in plain language, with its limit.
