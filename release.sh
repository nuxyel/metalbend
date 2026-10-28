#!/usr/bin/env bash
# The corpus on a new Bend release, against the release before it:
#   ./release.sh 2.0.40            # against 2.0.39
#   ./release.sh 2.0.40 2.0.38     # against another one
#   ./release.sh --previous 2.0.40 # only print the release it would compare against
# Builds each release from its tag in a clone of bendlang/bend ($BEND_SRC, build/bend by default, cloned if missing;
# fetched first) with bun, the way the released binary is built from the same source, behind a wrapper at build/bin/<n>; then
# runs the corpus on both at 1 and 16 threads (ROUNDS, 5 by default) into results/<date>-<new>/ and prints what moved
# beyond noise and any output that changed. A source build of 2.0.39 counts the same instructions as the release.
set -euo pipefail
cd "$(dirname "$0")"
previous_only=0
if [ "${1:-}" = --previous ]; then previous_only=1; shift; fi
new=${1:?usage: release.sh [--previous] <new version> [<old version>]}
src=${BEND_SRC:-$PWD/build/bend}
[ -d "$src/.git" ] || git clone -q https://github.com/bendlang/bend "$src"
git -C "$src" fetch -q --tags origin
git -C "$src" rev-parse -q --verify "refs/tags/v$new" > /dev/null || { echo "no tag v$new in bendlang/bend yet" >&2; exit 2; }
# the release before: the release tags (vX.Y.Z, no pre-releases) in version order, the one before $new
old=${2:-$(git -C "$src" tag -l 'v*' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sed 's/^v//' | sort -V |
  awk -v n="$new" '$0 == n {print prev; exit} {prev = $0}')}
[ -n "$old" ] || { echo "no release before $new" >&2; exit 2; }
git -C "$src" rev-parse -q --verify "refs/tags/v$old" > /dev/null || { echo "no tag v$old in bendlang/bend" >&2; exit 2; }
if [ "$previous_only" = 1 ]; then echo "$old"; exit 0; fi
mkdir -p build/bin build/src
# versions run.sh knows as installed releases go back to those when release.sh ends, failed or not: their source
# wrappers and builds would otherwise shadow the installed binaries in every later run.sh
cleanup() {
  for v in "$old" "$new"; do
    n=${v##*.}
    if [ "$n" -ge 35 ] && [ "$n" -le 39 ]; then rm -rf "build/bin/$n" "build/$n"; fi
  done
}
trap cleanup EXIT
for v in "$old" "$new"; do
  n=${v##*.}
  wt=$PWD/build/src/$v
  if [ ! -d "$wt" ]; then
    git -C "$src" worktree add -q --detach "$wt" "v$v"
    (cd "$wt/bend2/pack" && bun install --frozen-lockfile > /dev/null)
  fi
  printf '#!/bin/sh\nexec bun %s/bend2/main.ts "$@"\n' "$wt" > "build/bin/$n"
  chmod +x "build/bin/$n"
  echo "Bend $v: $("build/bin/$n" version)"
done
# a fresh build of every workload with both, so no binary from another build of the same number is reused
for v in "$old" "$new"; do rm -rf "build/${v##*.}"; done
OUT=${OUT:-results/$(date +%F)-$new} VERSIONS="${old##*.} ${new##*.}" THREADS=${THREADS:-"1 16"} ./run.sh > /dev/null
out=${OUT:-results/$(date +%F)-$new}
echo "== $out/summary.md"
sed -n '/## Beyond noise or differing outputs/,$p' "$out/summary.md"
[ "${ROUNDS:-5}" -ge 3 ] || echo "(fewer than 3 rounds: nothing is marked beyond noise; the tables are in $out/summary.md)"
