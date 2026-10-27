#!/usr/bin/env bash
# The corpus on a new Bend release, against the release before it:
#   ./release.sh 2.0.40            # against 2.0.39
#   ./release.sh 2.0.40 2.0.38     # against another one
# Builds each release from its tag in a clone of bendlang/bend ($BEND_SRC, build/bend by default, cloned if missing;
# fetched first) with bun, the way the released binary is built from the same source, behind a wrapper at build/bin/<n>; then
# runs the corpus on both at 1 and 16 threads (ROUNDS, 5 by default) into results/<date>-<new>/ and prints what moved
# beyond noise and any output that changed. A source build of 2.0.39 counts the same instructions as the release.
set -euo pipefail
cd "$(dirname "$0")"
new=${1:?usage: release.sh <new version> [<old version>]}
src=${BEND_SRC:-$PWD/build/bend}
[ -d "$src/.git" ] || git clone -q https://github.com/bendlang/bend "$src"
git -C "$src" fetch -q --tags origin
git -C "$src" rev-parse -q --verify "refs/tags/v$new" > /dev/null || { echo "no tag v$new in bendlang/bend yet" >&2; exit 2; }
old=${2:-$(git -C "$src" tag -l 'v2.0.*' | sed 's/^v//' | sort -t. -k3,3n | awk -v n="$new" '$0 == n {print prev; exit} {prev = $0}')}
[ -n "$old" ] || { echo "no release before $new" >&2; exit 2; }
git -C "$src" rev-parse -q --verify "refs/tags/v$old" > /dev/null || { echo "no tag v$old in bendlang/bend" >&2; exit 2; }
mkdir -p build/bin build/src
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
# versions run.sh knows as installed releases go back to those: drop their source wrappers and builds
for v in "$old" "$new"; do
  n=${v##*.}
  if [ "$n" -ge 35 ] && [ "$n" -le 39 ]; then rm -rf "build/bin/$n" "build/$n"; fi
done
echo "== $out/summary.md"
sed -n '/## Beyond noise or differing outputs/,$p' "$out/summary.md"
[ "${ROUNDS:-5}" -ge 3 ] || echo "(fewer than 3 rounds: nothing is marked beyond noise; the tables are in $out/summary.md)"
