# bpe-encode

A byte-level BPE tokenizer, trained and then used: 256 merges learned from a text of 4,096 words (about 22 KB), then a
second text of 32,768 words encoded with them into integer token ids. The algorithm is minbpe's, the one GPT-2's
tokenizer applies with its 50,000 rules; integer and list work, no floating point. The texts are synthetic: words from a
vocabulary of 64 made by a hash, picked with a skew toward the first ones, separated by spaces, so every machine
tokenizes the same text.

## Where it comes from

`bend-ml-bpe-tokenizer@0.1.3.0`'s `train` and `encode` (bend-ml), the tokenizer of bend-ml's GPT-2 demo.

## The C target

`native.c`: the same training and encoding as a C programmer writes them. The adjacent pairs are counted in a table
indexed by the two ids; the most frequent pair is merged (on a tie, the one that first appears in the text, the
package's rule), every occurrence left to right without overlap; encoding applies each rule in order. The same rules and
tokens, so the same output.

## The oracle

It prints the number of rules (256), the number of tokens (31,633) and an FNV-1a hash of the token ids (a byte as
itself, rule k as 256 + k): `770398c19951fa8c`.

## The mutants (`scripts/mutate.py`)

- one merge fewer: caught;
- C: a tie goes to the pair that appears last: caught;
- C: merges overlap: caught.
