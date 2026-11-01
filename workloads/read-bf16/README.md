# read-bf16

Two SmolLM2-135M decoder layers' weights (18 tensors, 7,080,192 numbers) read as BF16 from a 14 MB safetensors file, the
path a BendTorch model takes from a Hugging Face checkpoint: the JSON header lexed and parsed in Bend, then each tensor,
in the model's order (not the file's), read and widened exactly to F32 into one array.

The file is `data/bf16.safetensors`, written by `lib/gen_bf16.py` (`make data`; `run.sh` and `make check` write it when
it is missing). It is laid out as Hugging Face writes one: the header's length, the header padded with spaces, then each
tensor's bytes in the header's (sorted) order. Its numbers are `lib/mb.bend`'s values cut to BF16, so every machine
reads the same bits.

## Where it comes from

`bendtorch-load@1.2.0.0`'s `tensors` (BendTorch): the header is plain Bend, each tensor's bytes go through
`bend-ml-binary-read`'s BF16 effect, the contained workaround for the dense read Base lacks (bendlang/bend#1573).

## The C target

`native.c`: the header read and searched for each tensor in the model's order (its dtype, shape and `data_offsets`
checked), each tensor's numbers read with one `fread` and widened into the F32 array (the BF16 as the top 16 bits, the
low 16 zero), then the hash.

## The oracle

It prints the hash of the numbers: `d09cf49a5e86a7f6`.

## The mutants (`scripts/mutate.py`)

- the two layers read in the other order: caught;
- `k_proj` and `v_proj` swapped (same shape, other numbers): caught;
- C: a BF16 widened one bit short: caught;
- C: the data counted from the header's start: caught;
- `gen_bf16.py`: another seed, the file written again: caught.

It builds on Bend 2.0.36 and later; 2.0.35 cannot build it, like `read-binary`: the package's C effect does not compile
against that runtime.
