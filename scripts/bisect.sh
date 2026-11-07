#!/usr/bin/env bash
# The first bendlang/bend commit with a workload's new count: `git bisect run` over the commits between a good and a
# bad ref, each step a source build of Bend (scripts/bend_main.sh) and one Cachegrind count (scripts/count.sh), judged
# by scripts/bisect_report.py (bad when the count is nearer the bad end's than the good end's). Cachegrind's counts
# repeat exactly, so one count a step. Then the report: the commit, its pull request, the counts per function at its
# parent and at it, and the C both emit for the workload.
#   scripts/bisect.sh bpe-encode v2.0.39 v2.0.40 ir      # instructions
#   scripts/bisect.sh bpe-encode v2.0.39 v2.0.40 ir d1   # both, the counts of one shared by the other
#   scripts/bisect.sh bpe-encode v2.0.39 v2.0.40         # every metric that moved between the two (bits alone when
#                                                        # the bad end's output is not its oracle)
# OUT names the folder (build/bisect/<w>-<good>-<bad> by default): counts.tsv (every count taken), and per metric
# <metric>/ with steps.tsv, run.log and bisect.log (git's), the C of the parent and the commit (<commit12>.c),
# pr.tsv, and bisect_report.py's report.md, report.tsv, functions.tsv and c.diff. RUN gives the report a run's URL;
# PR_LOOKUP=0 skips asking GitHub for the pull request (gh api). The clone is $BEND_SRC (build/bend), as bend_main.sh's;
# each commit's tree stays under build/src, its wrapper at build/bin/at-<commit12>, its workload under build/count.
# Exits 0 when every bisect named a commit, 3 when nothing moved between the ends, 2 when an end gives no count.
set -uo pipefail
if [ "${1:-}" = --step ]; then
  # one step of `git bisect run`, in the bisect's worktree (checked out with --no-checkout: the commit is BISECT_HEAD)
  sha=$(git rev-parse BISECT_HEAD 2>/dev/null) || exit 128
  # git runs the step with the bisect's repository in GIT_DIR, which would turn every other git call to it
  unset GIT_DIR GIT_WORK_TREE GIT_COMMON_DIR GIT_INDEX_FILE GIT_PREFIX
fi
cd "$(dirname "$0")/.."
export BEND_NO_TELEMETRY=1
src=${BEND_SRC:-$PWD/build/bend}
safe() { echo "$1" | tr -c 'A-Za-z0-9._\n-' _; }

# a wrapper of Bend at a commit, built once (scripts/bend_main.sh keeps the tree by commit)
bend_at() {
  local c=$1 bin=build/bin/at-${1:0:12}
  if [ ! -x "$bin" ] || [ "$(cat "$bin.commit" 2>/dev/null)" != "$c" ]; then
    BIN=$bin scripts/bend_main.sh "$c" >> "$OUT/build.log" 2>&1 || return 1
  fi
  echo "$bin"
}
# the workload counted with one Bend, once: its row goes to counts.tsv; 1 when no count could be taken
count_with() {
  local bin=$1 commit=$2 label=$3
  awk -F'\t' -v c="$commit" '$2 == c {f = 1} END {exit !f}' "$OUT/counts.tsv" && return 0
  REF=$label scripts/count.sh "$bin" "$W" > "$OUT/row.tmp" 2>> "$OUT/build.log"
  [ $? = 2 ] && { rm -f "$OUT/row.tmp"; return 1; }
  cat "$OUT/row.tmp" >> "$OUT/counts.tsv"
  rm -f "$OUT/row.tmp"
}
row_of() { awk -F'\t' -v c="$1" '$2 == c' "$OUT/counts.tsv" | tail -1; }

if [ "${1:-}" = --step ]; then
  for v in W M OUT GOOD BAD STEPS; do [ -n "${!v:-}" ] || exit 128; done
  subject=$(git -C "$src" log -1 --format=%s "$sha" | tr '\t' ' ')
  step() { echo -e "$sha\t$1\t$2\t$3\t$4\t$5\t$subject" >> "$STEPS"; }
  bin=$(bend_at "$sha") || { step skip - - - "Bend does not build"; exit 125; }
  count_with "$bin" "$sha" "$sha" || { step skip - - - "no count"; exit 125; }
  IFS=$'\t' read -r verdict why < <(python3 -I scripts/bisect_report.py judge "$OUT/counts.tsv" "$M" "$GOOD" "$BAD" "$sha")
  r=$(row_of "$sha")
  step "${verdict:-skip}" "$(cut -f5 <<< "$r")" "$(cut -f6 <<< "$r")" "$(cut -f9 <<< "$r")" "${why:-no verdict}"
  case ${verdict:-} in good) exit 0 ;; bad) exit 1 ;; skip) exit 125 ;; *) exit 128 ;; esac
fi

W=${1:?usage: scripts/bisect.sh <workload> <good ref> <bad ref> [ir|d1|bits ...]}
good=${2:?usage: scripts/bisect.sh <workload> <good ref> <bad ref> [ir|d1|bits ...]}
bad=${3:?usage: scripts/bisect.sh <workload> <good ref> <bad ref> [ir|d1|bits ...]}
shift 3
[ -f "workloads/$W/main.bend" ] || { echo "no workload $W" >&2; exit 2; }
OUT=${OUT:-build/bisect/$(safe "$W")-$(safe "$good")-$(safe "$bad")}
mkdir -p "$OUT" && OUT=$(cd "$OUT" && pwd)
export OUT W
me=$PWD/scripts/bisect.sh
[ -f "$OUT/counts.tsv" ] || scripts/count.sh --header > "$OUT/counts.tsv"

# the two ends, each built from its ref and counted
for end in good bad; do
  ref=${!end}
  BIN=build/bin/at-$(safe "$ref") scripts/bend_main.sh "$ref" >> "$OUT/build.log" 2>&1 ||
    { echo "bisect.sh: no Bend at $ref" >&2; exit 2; }
  c=$(cat "build/bin/at-$(safe "$ref").commit")
  count_with "build/bin/at-$(safe "$ref")" "$c" "$ref" || { echo "bisect.sh: no count of $W on $ref" >&2; exit 2; }
  printf -v "${end}_sha" '%s' "$c"
done
# shellcheck disable=SC2154  # set by printf -v above
gsha=$good_sha bsha=$bad_sha
metrics=${*:-$(python3 -I scripts/bisect_report.py metrics "$OUT/counts.tsv" "$gsha" "$bsha")}
[ -n "$metrics" ] || { echo "$W: nothing moved from $good to $bad"; exit 3; }
n=$(git -C "$src" rev-list --count "$gsha..$bsha")
echo "$W: $n commits from $good (${gsha:0:12}) to $bad (${bsha:0:12}); bisecting $metrics"

st=0
for m in $metrics; do
  case $m in ir|d1|bits) ;; *) echo "bisect.sh: no metric $m (ir, d1 or bits)" >&2; exit 2 ;; esac
  d=$OUT/$m
  mkdir -p "$d"
  echo -e "commit\tverdict\tir\td1_misses\tbits\twhy\tsubject" > "$d/steps.tsv"
  wt=$PWD/build/src/bisect-$(safe "$W")-$m
  git -C "$src" worktree remove --force "$wt" 2> /dev/null
  git -C "$src" worktree prune
  git -C "$src" worktree add -q --detach --no-checkout "$wt" "$bsha"
  (cd "$wt" && git bisect start --no-checkout "$bsha" "$gsha" > /dev/null &&
    M=$m GOOD=$gsha BAD=$bsha STEPS=$d/steps.tsv git bisect run "$me" --step) \
    > "$d/run.log" 2>&1
  first=$(git -C "$wt" rev-parse -q --verify refs/bisect/bad)
  candidates=()
  if ! grep -qE "is the first '?bad'? commit" "$d/run.log"; then
    # only skipped commits left between the last good and the first bad: git lists the candidates
    mapfile -t candidates < <(sed -n '/could be any of/,$p' "$d/run.log" | grep -oE '^[0-9a-f]{40}')
    st=1
  fi
  git -C "$wt" bisect log > "$d/bisect.log" 2>&1
  git -C "$wt" bisect reset -q > /dev/null 2>&1
  git -C "$src" worktree remove --force "$wt"
  [ -n "$first" ] || { echo "bisect.sh: $W $m: the bisect named no commit (run.log)" >&2; st=1; continue; }
  parent=$(git -C "$src" rev-parse "$first^")
  for c in "$parent" "$first"; do
    bin=$(bend_at "$c") || { echo "bisect.sh: Bend does not build at $c" >&2; continue; }
    count_with "$bin" "$c" "$c" || echo "bisect.sh: no count of $W at $c" >&2
    (cd "workloads/$W" && "$OLDPWD/$bin" main.bend -o "$d/${c:0:12}.c") >> "$d/emit.log" 2>&1 ||
      echo "bisect.sh: no C from Bend at $c" >&2
  done
  : > "$d/pr.tsv"
  [ "${PR_LOOKUP:-1}" = 0 ] || gh api "repos/bendlang/bend/commits/$first/pulls" \
    --jq '.[0] | select(.) | [.number, .title, .html_url] | @tsv' > "$d/pr.tsv" 2>> "$d/run.log" || : > "$d/pr.tsv"
  python3 -I scripts/bisect_report.py report "$d" --workload "$W" --metric "$m" --good "$good" --bad "$bad" \
    --counts "$OUT/counts.tsv" --steps "$d/steps.tsv" --first "$first" --parent "$parent" \
    --subject "$(git -C "$src" log -1 --format=%s "$first")" --pr "$d/pr.tsv" --cg-dir build/count \
    --candidates "${candidates[*]}" --commits "$n" ${RUN:+--run "$RUN"} || st=1
done
exit "$st"
