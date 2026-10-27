# read-binary: 4,194,304 F32 (16 MB, data/dense.bin from lib/gen_dense.py) read into an Array with bend-ml-binary-read,
# the C library effect that stands in for a dense read in Base (bendlang/bend#1573). Prints the hash of the numbers.
import Base
import bend-ml-binary-read@0.2.0.0/main.bend as R
import ../../lib/mb.bend as MB

def fin(r: File & (Array<F32> & Result<&1, &1, U32 & String, U32>)) -> IO(Unit):
  match r:
    case Tuple{f, Tuple{a, res}}: MB.show_hash(MB.hash(4194304n, a))

def main() -> IO(Unit):
  do IO<Unit>:
    f : File <- IO.try(File, File.open("data/dense.bin", "r"))
    r : File & (Array<F32> & Result<&1, &1, U32 & String, U32>) <- R.read_f32(f, 0, 4194304, Array.new(F32, 22n, 0.0))
    fin(r)
