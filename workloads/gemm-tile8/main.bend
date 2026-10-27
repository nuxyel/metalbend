# gemm-tile8: tensor-array's products, sequential (par 0), 8 repetitions of each shape (lib/gemm.bend).
import Base
import ../../lib/gemm.bend as G

def main() -> IO(Unit):
  G.run(8n, 0n)
