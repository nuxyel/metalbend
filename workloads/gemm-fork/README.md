# gemm-fork

`gemm-tile8`'s three products, through tensor-fork's parallel blocks instead of tensor-array's sequential loop: up to 8
blocks a product (`par 3`, the split BendTorch uses), each block a tensor-array product on its part of C. It runs on 1
and 16 threads; on one thread it measures what the fork path itself costs, on 16 how far it scales.

## Where it comes from

`bend-ml-tensor-fork@0.1.4.0` over `bend-ml-tensor-array@0.1.16.0` (bend-ml), through `lib/gemm_fork.bend`. tensor-fork
shares the operands between the blocks with `@unsafe` code, which Bend's compiler does not check yet; the laws below
cover a model of it.

## The C target

`native.c`: the same products and the same cells, in tensor-fork's blocks. Each product splits into 8 blocks, halved at
each node as tensor-fork halves them: by rows when C has at least as many rows as columns (`tn`), by columns otherwise
(`nt` and `nn`). A block of columns runs every row of C over its own columns only, so its packed lines of B (442 KB
here) stay in the cache, where `gemm-tile8`'s order streams all of B (3.5 MB) once per row of C. Every cell is the same
dot as `gemm-tile8`'s, added once into C, so the bits are the same. It runs the blocks one after another on one thread.

## The oracle

`0c6d7fee9a7ddf37`, `gemm-tile8`'s hash: tensor-fork's blocks give the same bits at any depth.

## The mutants (`scripts/mutate.py`)

- one repetition fewer: caught;
- two levels of parallel blocks instead of three: survives, and must: the blocks give the same bits at any depth (the
  reason `gemm-fork` and `gemm-tile8` share an oracle);
- C: a column block leaves out its last column: caught.

## The laws

`fork_cover` (the split visits every row or column once, in order; a model of the split) and `t8_rows_split`,
`t8_blocks` (row blocks run one after another compute tensor-array's sequential product, on its own code). What they do
not prove (parallel against sequential, the U32 offsets, the column splits) is in `laws/README.md`.

## Probes

`probes/l3/` counts this workload and `gemm-tile8` against their C targets with the L3 cache loaded by other cores.
