#!/usr/bin/env bash
# Two Bends on the corpus under Cachegrind, on one machine: each Bend built once from its ref (scripts/bend_main.sh),
# every workload counted with both (scripts/count.sh), then compared (scripts/track_verdict.py). The release watch
# (.github/workflows/track.yml) runs it on GitHub's runners for each new release of bendlang/bend, one job a workload.
#   scripts/track.sh v2.0.39 v2.0.40                    # every workload, into build/track/v2.0.39-v2.0.40/
#   scripts/track.sh v2.0.39 v2.0.40 bpe-encode adamw   # some
#   scripts/track.sh --next v2.0.39       # the comparison after release v2.0.39 ("v2.0.39 v2.0.40"), or nothing
#   scripts/track.sh --previous v2.0.40   # the release before v2.0.40
# OUT names the folder: counts.tsv (count.sh's rows, both Bends), env.tsv, then track_verdict.py's verdict.tsv and
# report.md, and issue.md with issue-title.txt on a regression or a changed output. RUN and STORE give the report a
# run's URL and the counts' place on the data branch. Releases are bendlang/bend's tags vX.Y.Z in version order
# (BEND_REMOTE for another remote). Exits 0 when every count was taken, findings or not; 2 when a Bend cannot be
# built or a count could not be taken.
set -uo pipefail
cd "$(dirname "$0")/.."
remote=${BEND_REMOTE:-https://github.com/bendlang/bend}
releases() {
  git ls-remote --tags "$remote" 'v*' | sed -n 's|.*refs/tags/\(v[0-9]*\.[0-9]*\.[0-9]*\)$|\1|p' | sort -V
}
case ${1:-} in
  --previous)
    releases | awk -v n="${2:?usage: track.sh --previous <release>}" '$0 == n {print prev; exit} {prev = $0}'
    exit 0 ;;
  --next)
    # the first release after $2 and the one before it (normally $2 itself)
    releases | awk -v l="${2:?usage: track.sh --next <release>}" '
      { if (seen && !done) { print prev " " $0; done = 1 } if ($0 == l) seen = 1; prev = $0 }'
    exit 0 ;;
esac
old=${1:?usage: scripts/track.sh <old ref> <new ref> [workloads...]}
new=${2:?usage: scripts/track.sh <old ref> <new ref> [workloads...]}
shift 2
ws=${*:-$(ls workloads)}
safe() { echo "$1" | tr -c 'A-Za-z0-9._\n-' _; }
OUT=${OUT:-build/track/$(safe "$old")-$(safe "$new")}
mkdir -p "$OUT"
for ref in "$old" "$new"; do
  BIN=build/bin/at-$(safe "$ref") scripts/bend_main.sh "$ref" >&2 || { echo "track.sh: no Bend at $ref" >&2; exit 2; }
done
{
  echo -e "key\tvalue"
  echo -e "date\t$(date -Is)"
  echo -e "old\t$old"
  echo -e "old_commit\t$(cat "build/bin/at-$(safe "$old").commit")"
  echo -e "new\t$new"
  echo -e "new_commit\t$(cat "build/bin/at-$(safe "$new").commit")"
  echo -e "cpu\t$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo -e "runner\t${RUNNER_OS:+GitHub Actions, ${ImageOS:-} ${ImageVersion:-}}"
  echo -e "clang\t$(clang --version 2>/dev/null | head -1)"
  echo -e "valgrind\t$(valgrind --version 2>/dev/null)"
  echo -e "bun\t$(bun --version 2>/dev/null)"
  echo -e "metalbend\t$(git rev-parse --short HEAD 2>/dev/null)$(git diff --quiet 2>/dev/null || echo -dirty)"
  echo -e "run\t${RUN:-}"
} > "$OUT/env.tsv"
counts=$OUT/counts.tsv
scripts/count.sh --header > "$counts"
st=0
for w in $ws; do
  for ref in "$old" "$new"; do
    REF=$ref scripts/count.sh "build/bin/at-$(safe "$ref")" "$w" >> "$counts"
    case $? in
      0) ;;
      1|3|4) echo "track.sh: $w on $ref: $(tail -1 "$counts" | cut -f9)" >&2 ;;
      *) echo "track.sh: no count of $w on $ref" >&2; st=2 ;;
    esac
  done
done
python3 -I scripts/track_verdict.py "$counts" "$old" "$new" "$OUT" ${RUN:+--run "$RUN"} ${STORE:+--store "$STORE"}
exit "$st"
