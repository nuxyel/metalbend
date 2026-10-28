# The GPU lane's toolkit and device, sourced by scripts/check_oracles.sh and run.sh (for workloads/<name>/gpu.bend).
# `bend x.bend -o x` builds the device program too (x.gpu, next to x) when CUDA_HOME names a toolkit with nvrtc.h, and
# a CPU-only binary otherwise, with no error; so a GPU build is checked to link libnvrtc before it counts as one.
# CUDA_HOME: the first of CUDA_HOME and these that holds include/nvrtc.h (BendTorch's order).
for c in "${CUDA_HOME:-}" "$HOME/.local/cuda12" "${CUDA_PATH:-}" /usr/local/cuda /opt/cuda; do
  if [ -n "$c" ] && [ -f "$c/include/nvrtc.h" ]; then CUDA_HOME=$c; break; fi
done
[ -f "${CUDA_HOME:-}/include/nvrtc.h" ] || CUDA_HOME=
export CUDA_HOME
# the libraries are in lib64 or lib, by the toolkit's layout
if [ -n "$CUDA_HOME" ]; then
  if [ -d "$CUDA_HOME/lib64" ]; then CUDA_LIB=$CUDA_HOME/lib64; else CUDA_LIB=$CUDA_HOME/lib; fi
  export LD_LIBRARY_PATH=$CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
fi

# why there is no GPU lane here, or nothing when there is one: a toolkit with nvrtc.h and a device the driver sees
gpu_missing() {
  if [ -z "$CUDA_HOME" ]; then
    echo "no CUDA toolkit (no include/nvrtc.h in CUDA_HOME, ~/.local/cuda12, CUDA_PATH, /usr/local/cuda or /opt/cuda)"
  elif ! command -v nvidia-smi > /dev/null; then echo "no nvidia-smi, so no NVIDIA driver"
  elif ! nvidia-smi -L 2>/dev/null | grep -q '^GPU '; then echo "nvidia-smi sees no GPU"
  fi
}

# builds workloads/$1/gpu.bend with Bend $2 into $3 (and $3.gpu); fails on a binary that does not link libnvrtc
gpu_build() {
  (cd "workloads/$1" && CUDA_HOME=$CUDA_HOME "$2" gpu.bend -o "$3") && ldd "$3" | grep -q libnvrtc
}
