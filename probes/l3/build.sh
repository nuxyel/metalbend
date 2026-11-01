#!/usr/bin/env bash
# Builds the probe's binaries into build/l3/ (no step by hand) and prints the four measured ones, one per line:
#   probes/l3/build.sh [<bend>] [<tag>]     # default ~/.bend-2.0.39/bin/bend, tag 39
# gemm-fork-<tag> and gemm-tile8-<tag> are the workloads as run.sh builds them (from inside their folders);
# gemm-fork-c and gemm-tile8-c their C targets with the flags `bend -o` gives clang; stream is the antagonist.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
bend=${1:-$HOME/.bend-2.0.39/bin/bend}
tag=${2:-39}
case $bend in */*) bend=$(realpath "$bend") ;; esac
out=$root/build/l3
mkdir -p "$out"
export BEND_NO_TELEMETRY=1
for w in gemm-fork gemm-tile8; do
  if ! (cd "$root/workloads/$w" && "$bend" main.bend -o "$out/$w-$tag") > "$out/$w-$tag.log" 2>&1; then
    echo "build of $w with $bend failed: $(tail -c 400 "$out/$w-$tag.log")" >&2
    exit 1
  fi
  clang -std=c11 -O3 "$root/workloads/$w/native.c" -o "$out/$w-c" -lm
  echo "$out/$w-$tag"
  echo "$out/$w-c"
done
clang -O2 "$here/stream.c" -o "$out/stream"
