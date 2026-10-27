# gemm-fork: the same products through tensor-fork in up to 8 blocks (par 3, BendTorch's split), run on one thread: the
# cost of the shared-operand fork path itself (lib/gemm_fork.bend). Must print gemm-tile8's hashes.
import Base
import ../../lib/gemm_fork.bend as G

def main() -> IO(Unit):
  G.run(8n, 3n)
