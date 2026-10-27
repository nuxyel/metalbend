# read-native: the same 4,194,304 F32 as read-binary, read with Base's File.read_at in blocks of 1 MB: each block is a
# list with one cell per byte, decoded four bytes at a time into the Array (the bitcast of bend-ml's GPT-2 loader).
# The path Taelin called a bug in the language (2026-10-16); bendlang/bend#1573 asks for a dense read. Prints the
# hash of the numbers, which must equal read-binary's.
import Base
import ../../lib/mb.bend as MB

# four little-endian bytes per number, into cells i..
def put(bs: List<&2, U32>, +i: U32, a: Array<F32>) -> Array<F32>:
  match bs:
    case Con{b0, Con{b1, Con{b2, Con{b3, t}}}}: put(t, (i + 1 : U32), Array.set(F32, a, i, MB.u2f((b0 + (b1 * 256 : U32) + (b2 * 65536 : U32) + (b3 * 16777216 : U32) : U32))))
    case _: a

# one block read: its bytes decoded into the array at byte off, then k with the file and the array
def after(m: File & Result<&1, &1, U32 & String, List<&2, U32>>, +off: U32, a: Array<F32>, k: File -> Array<F32> -> IO(Array<F32>)) -> IO(Array<F32>):
  match m:
    case Tuple{f2, Done{bs}}: k(f2)(put(bs, (off / 4 : U32), a))
    case Tuple{f2, Fail{e}}: IO.pure(Array<F32>, a)

# blocks of 1 MB from byte off
def blocks(left: Nat, +off: U32, f: File, a: Array<F32>) -> IO(Array<F32>):
  match left:
    case 0n: IO.pure(Array<F32>, a)
    case 1n+q: IO.bind(File & Result<&1, &1, U32 & String, List<&2, U32>>, Array<F32>, File.read_at(f, off, 1048576), m => after(m, off, a, f2 => a2 => blocks(q, (off + 1048576 : U32), f2, a2)))

def main() -> IO(Unit):
  do IO<Unit>:
    f : File <- IO.try(File, File.open("data/dense.bin", "r"))
    a : Array<F32> <- blocks(16n, 0, f, Array.new(F32, 22n, 0.0))
    MB.show_hash(MB.hash(4194304n, a))
