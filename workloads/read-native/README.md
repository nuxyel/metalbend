# read-native

Reading model weights from a file: 4,194,304 F32 numbers (16 MB, `data/dense.bin`) into an `Array`, with Base's
`File.read_at` in blocks of 1 MB. Each block comes back as a list with one cell per byte, decoded four bytes at a time
into the array (the bitcast of bend-ml's GPT-2 loader). This is the path Victor Taelin called a bug in the language
(2026-10-16); bendlang/bend#1573 asks for a dense read.

## Where it comes from

Base's `File.read_at` and the decoding of bend-ml's GPT-2 loader; `read-binary` reads the same file through
`bend-ml-binary-read`. The workload imports no package: only Base and `lib/mb.bend`. `data/dense.bin` comes from
`lib/gen_dense.py` (`make data`, or `run.sh` when it is missing), a fixed seed, the same file on every machine.

## The C target

`native.c`: one `fread` of the 16 MB into an array of F32, then the same hash. `read-binary` uses it too.

## The oracle

It prints the hash of the numbers: `9b44f947a6f6c6b9`, which `read-binary` must print too.

## The mutants (`scripts/mutate.py`)

- one block fewer: caught;
- C: the hash skips the last cell: caught;
- `lib/gen_dense.py` with another seed (the file written again): caught;
- `lib/mb.bend`: the hash starts at cell 1: caught.
