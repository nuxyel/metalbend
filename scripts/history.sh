#!/usr/bin/env bash
# One workload counted under Cachegrind with every Bend release of a range, one after another on one machine
# (scripts/count.sh each), so the workload's whole line comes from one runner and one clang. The history workflow
# (.github/workflows/history.yml) runs it on GitHub's runners, one job a workload; scripts/history_report.py and
# scripts/history_chart.py read what it writes.
#   scripts/history.sh --releases v2.0.32 v2.0.40      # bendlang/bend's release tags from..to, in version order
#   scripts/history.sh adamw v2.0.32 v2.0.33 v2.0.34   # adamw on those, into build/history/adamw/
#   OUT=out scripts/history.sh bpe-encode $(scripts/history.sh --releases v2.0.32 v2.0.40)
# OUT gets counts.tsv (count.sh's rows, one a release, named by the release), gaps.tsv (release, workload, bits, why:
# the first error line of a build or a run that failed, for a release where the workload does not build or run) and
# env.tsv. Each Bend is built from its tag by scripts/bend_main.sh into build/bin/at-<release>, or taken as it is
# when NO_BUILD=1 and that wrapper exists. Releases are bendlang/bend's tags vX.Y.Z (BEND_REMOTE for another remote).
# Exits 0 when every release gave a row, the failures recorded as gaps; 2 when a Bend cannot be built or counted.
set -uo pipefail
cd "$(dirname "$0")/.."
remote=${BEND_REMOTE:-https://github.com/bendlang/bend}
if [ "${1:-}" = --releases ]; then
  from=${2:?usage: history.sh --releases <first> <last>}
  to=${3:?usage: history.sh --releases <first> <last>}
  git ls-remote --tags "$remote" 'v*' | sed -n 's|.*refs/tags/\(v[0-9]*\.[0-9]*\.[0-9]*\)$|\1|p' | sort -V |
    awk -v a="$from" -v b="$to" '$0 == a {on = 1} on {print} $0 == b {exit}'
  exit 0
fi
w=${1:?usage: scripts/history.sh <workload> <release>...}
shift
[ $# -gt 0 ] || { echo "usage: scripts/history.sh <workload> <release>..." >&2; exit 2; }
[ -f "workloads/$w/main.bend" ] || { echo "no workload $w" >&2; exit 2; }
safe() { echo "$1" | tr -c 'A-Za-z0-9._\n-' _; }
OUT=${OUT:-build/history/$w}
mkdir -p "$OUT"
{
  echo -e "key\tvalue"
  echo -e "date\t$(date -Is)"
  echo -e "workload\t$w"
  echo -e "releases\t$*"
  echo -e "cpu\t$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo -e "runner\t${RUNNER_OS:+GitHub Actions, ${ImageOS:-} ${ImageVersion:-}}"
  echo -e "clang\t$(clang --version 2>/dev/null | head -1)"
  echo -e "valgrind\t$(valgrind --version 2>/dev/null)"
  echo -e "bun\t$(bun --version 2>/dev/null)"
  echo -e "metalbend\t$(git rev-parse --short HEAD 2>/dev/null)$(git diff --quiet 2>/dev/null || echo -dirty)"
  echo -e "run\t${RUN:-}"
} > "$OUT/env.tsv"
scripts/count.sh --header > "$OUT/counts.tsv"
echo -e "release\tworkload\tbits\twhy" > "$OUT/gaps.tsv"
st=0
for rel in "$@"; do
  bend=build/bin/at-$(safe "$rel")
  if [ "${NO_BUILD:-0}" != 1 ] || [ ! -x "$bend" ]; then
    BIN=$bend scripts/bend_main.sh "$rel" >&2 || { echo "history.sh: no Bend at $rel" >&2; st=2; continue; }
  fi
  REF=$rel scripts/count.sh "$bend" "$w" >> "$OUT/counts.tsv"
  case $? in
    0|1) ;;
    3|4)
      # the log count.sh just wrote: the build's for a failed build, the run's report for a failed run
      bits=$(tail -1 "$OUT/counts.tsv" | cut -f9)
      if [ "$bits" = compile-failed ]; then log=$(ls -t build/count/*/"$w".log 2>/dev/null | head -1)
      else log=$(ls -t build/count/*/"$w".cg 2>/dev/null | head -1); fi
      why=$(grep -m1 -i -E 'error|cannot|failed|undefined|unbound|expected' "${log:-/dev/null}" 2>/dev/null |
        sed -E 's|/tmp/bend-[A-Za-z0-9]+/||g' | tr '\t' ' ' | cut -c1-200)
      echo -e "$rel\t$w\t$bits\t${why:-see the build log}" >> "$OUT/gaps.tsv"
      echo "history.sh: $w on $rel: $bits" >&2 ;;
    *) echo "history.sh: no count of $w on $rel" >&2; st=2 ;;
  esac
done
exit "$st"
