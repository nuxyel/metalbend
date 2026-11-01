#!/usr/bin/env bash
# Builds Bend from a ref of bendlang/bend (origin/main by default) into build/bin/main, the way release.sh builds a
# release from its tag: a tree of the clone at build/src/main-<commit>, `bun install --frozen-lockfile`, and a wrapper
# that runs its bend2/main.ts. The commit goes to build/bin/main.commit (and run.sh's env.tsv reads it from the wrapper).
#   scripts/bend_main.sh                  # origin/main, fetched first
#   scripts/bend_main.sh <ref>            # a branch of origin, a tag or a commit
#   BEND=build/bin/main ANY_BEND=1 make check     # then: the bits on main (it may not report a new version yet)
# The clone is $BEND_SRC (build/bend by default, cloned if missing), shared with release.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
ref=${1:-main}
src=${BEND_SRC:-$PWD/build/bend}
[ -d "$src/.git" ] || git clone -q https://github.com/bendlang/bend "$src"
git -C "$src" fetch -q --tags origin
# a branch name is origin's branch, never a stale local one
commit=$(git -C "$src" rev-parse -q --verify "refs/remotes/origin/$ref^{commit}" ||
  git -C "$src" rev-parse -q --verify "$ref^{commit}") || { echo "no ref $ref in bendlang/bend" >&2; exit 2; }
mkdir -p build/bin build/src
git -C "$src" worktree prune
wt=$PWD/build/src/main-${commit:0:8}
if [ ! -d "$wt" ]; then
  git -C "$src" worktree add -q --detach "$wt" "$commit"
  (cd "$wt/bend2/pack" && bun install --frozen-lockfile > /dev/null)
fi
printf '#!/bin/sh\nexec bun %s/bend2/main.ts "$@"\n' "$wt" > build/bin/main
chmod +x build/bin/main
echo "$commit" > build/bin/main.commit
echo "Bend $ref at $(git -C "$src" log -1 --format='%h (%cs) %s' "$commit"): build/bin/main reports $(BEND_NO_TELEMETRY=1 build/bin/main version)"
