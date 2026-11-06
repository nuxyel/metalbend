#!/usr/bin/env bash
# Builds the probe's binaries with one Bend, and the C versions, into build/p1781/ (no step by hand):
#   probes/1781/build.sh <bend> <tag>     # e.g. ~/.bend-2.0.39/bin/bend 39, or build/bin/main main
# prints the paths built, one per line, for count.sh:
#   ROUNDS=5 probes/1781/count.sh $(probes/1781/build.sh <bend> <tag>) > probes/1781/results/<file>.tsv
# The checked loops build on any Bend: dot_checked-<tag>, matvec-<tag>, gemm-<tag> (the workloads as published),
# matvec_km1-<tag>. The unchecked ones need Array.get_unchecked (bendlang/bend#1880, a888ef27): dot_unchecked,
# dot_km1_unchecked, matvec_u, matvec_u0, gemm_u; on a Bend without it they are skipped, and said so on stderr. The C
# versions (dot-c, matvec-c, gemm-c) are built once. The variants are gen.py's, from tensor-array 0.1.16.0 as the
# BendHub store has it (BEND_LIB, ~/.bend/lib), which the build of matvec-bands fetches first.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
bend=${1:?usage: probes/1781/build.sh <bend> <tag>}
tag=${2:?usage: probes/1781/build.sh <bend> <tag>}
case $bend in */*) bend=$(realpath "$bend") ;; esac
out=$root/build/p1781
mkdir -p "$out"
export BEND_NO_TELEMETRY=1

# builds <dir>/<file> into $out/<name>; a failure stops the script, with the log's end
build() {
  local dir=$1 file=$2 name=$3
  if ! (cd "$dir" && "$bend" "$file" -o "$out/$name") > "$out/$name.log" 2>&1; then
    echo "build of $name failed: $(tail -c 400 "$out/$name.log")" >&2
    return 1
  fi
  echo "$out/$name"
}

# the checked loops, as published: the matvec-bands build also puts tensor-array 0.1.16.0 in the store for gen.py
build "$root/workloads/matvec-bands" main.bend "matvec-$tag"
build "$root/workloads/gemm-tile8" main.bend "gemm-$tag"
build "$here" dot_checked.bend "dot_checked-$tag"
lib=${BEND_LIB:-$HOME/.bend/lib}
ta=$lib/$(cat "$lib/names/bend-ml-tensor-array@0.1.16.0")/main.bend
python3 -I "$here/gen.py" "$ta" > /dev/null
src=$out/src
build "$src/km1/workloads/matvec-bands" main.bend "matvec_km1-$tag"

# the unchecked loops, when this Bend has Array.get_unchecked (tried on the smallest of them)
if (cd "$here" && "$bend" dot_unchecked.bend -o "$out/dot_unchecked-$tag") > "$out/dot_unchecked-$tag.log" 2>&1; then
  echo "$out/dot_unchecked-$tag"
  build "$here" dot_km1_unchecked.bend "dot_km1_unchecked-$tag"
  build "$src/u/workloads/matvec-bands" main.bend "matvec_u-$tag"
  build "$src/u0/workloads/matvec-bands" main.bend "matvec_u0-$tag"
  build "$src/u/workloads/gemm-tile8" main.bend "gemm_u-$tag"
else
  echo "Bend $tag ($("$bend" version 2>/dev/null)) did not build dot_unchecked.bend (no Array.get_unchecked?):" \
    "the unchecked variants are skipped; $out/dot_unchecked-$tag.log has why" >&2
fi

# the C versions, with the flags `bend -o` gives clang
for c in "dot:$here/dot.c" "matvec:$root/workloads/matvec-bands/native.c" "gemm:$root/workloads/gemm-tile8/native.c"; do
  if [ ! -x "$out/${c%%:*}-c" ] || [ "${c#*:}" -nt "$out/${c%%:*}-c" ]; then
    clang -std=c11 -O3 "${c#*:}" -o "$out/${c%%:*}-c" -lm
  fi
  echo "$out/${c%%:*}-c"
done
