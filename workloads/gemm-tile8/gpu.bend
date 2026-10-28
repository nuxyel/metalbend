# gemm-tile8's GPU target: the same products through tensor-gpu 0.1.4.0 (tensor-array 0.1.16.0's products, one bang
# each, on the GPU in a build with CUDA and on the CPU threads otherwise; lib/gemm_gpu.bend). Must print gemm-tile8's
# hashes: tensor-gpu keeps tensor-array's four partial sums and Bend builds the device code without fused multiply-add.
import Base
import ../../lib/gemm_gpu.bend as G

def main() -> IO(Unit):
  G.run(8n, 0n)
