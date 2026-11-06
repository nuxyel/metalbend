#!/usr/bin/env bash
# Launch day on one Bend release, in order (plan v1, step 8):
#   scripts/launch.sh 2.0.40                      # or: make launch VERSION=2.0.40
#   BUSY_OK=1 ROUNDS=1 OUT=<scratch dir> scripts/launch.sh 2.0.39   # a rehearsal: bits only, its timings thrown away
# 1. scripts/preflight.sh: stops on a busy machine (BUSY_OK=1 runs anyway; the run is then marked busy everywhere);
# 2. make check-gpu: the GPU targets' bits with the pinned Bend (skipped, with the reason, with no GPU);
# 3. GPU=1 ./release.sh <version>: the corpus on the release and the one before, into OUT (results/<date>-<version>);
# 4. the #1781 probe (probes/1781/), only when the release contains a888ef27 (Array.get_unchecked): its binaries
#    built with both versions and counted PROBE_ROUNDS times (5) into OUT/probe-1781.tsv;
# 5. scripts/chart.py: docs/results-<version>.svg when OUT is under results/, OUT/results-<version>.svg otherwise;
# 6. scripts/report.py: OUT/report.md, the numbers the posts need.
# A hash that is not its oracle does not stop it (it is a finding, in oracles.txt and the report); it exits 1 at the end.
set -euo pipefail
cd "$(dirname "$0")/.."
new=${1:?usage: scripts/launch.sh <version>}
out=${OUT:-results/$(date +%F)-$new}
say() { printf '\n== %s\n' "$*"; }
name() { case $1 in 2.0.*) echo "${1##*.}" ;; *) echo "$1" ;; esac; }

say "preflight"
if ! scripts/preflight.sh; then
  [ "${BUSY_OK:-0}" = 1 ] || { echo "launch: stopping on a busy machine (BUSY_OK=1 to run anyway, marked busy)"; exit 1; }
  echo "launch: BUSY_OK=1, going on; every timing of this run is a diagnosis"
fi

say "make check-gpu"
env -u OUT make check-gpu  # check_oracles.sh builds into $OUT and clears it first: never the run's folder

say "GPU=1 ./release.sh $new -> $out"
st=0
OUT=$out GPU=1 ./release.sh "$new" || st=$?
# 1 is a hash that is not its oracle, a finding; anything else (or no oracles.txt, which run.sh writes last) stopped it
[ "$st" -le 1 ] && [ -f "$out/oracles.txt" ] || { echo "launch: release.sh stopped (exit $st)"; exit "$st"; }
old=$(./release.sh --previous "$new")

say "probe #1781"
src=${BEND_SRC:-$PWD/build/bend}
# a888ef27: bendlang/bend#1880, Array.get_unchecked (PROBE_COMMIT is for the tests)
if git -C "$src" merge-base --is-ancestor "${PROBE_COMMIT:-a888ef27}" "v$new" 2>/dev/null; then
  bins=()
  for v in "$old" "$new"; do
    n=$(name "$v")
    # the source build release.sh made, or the installed release when release.sh dropped its wrapper (35-39)
    bend=$PWD/build/bin/$n
    [ -x "$bend" ] || bend=$HOME/.bend-$v/bin/bend
    mapfile -t -O "${#bins[@]}" bins < <(probes/1781/build.sh "$bend" "$n")
  done
  mapfile -t bins < <(printf '%s\n' "${bins[@]}" | awk '!seen[$0]++')
  ROUNDS=${PROBE_ROUNDS:-5} probes/1781/count.sh "${bins[@]}" > "$out/probe-1781.tsv"
  python3 -I probes/1781/summarize.py "$out/probe-1781.tsv"
else
  echo "v$new does not contain a888ef27 (Array.get_unchecked): not timed"
fi

say "chart"
full=$new
case $(realpath -m "$out") in "$PWD"/results/*) svg=docs/results-$full.svg ;; *) svg=$out/results-$full.svg ;; esac
python3 -I scripts/chart.py "$(name "$new")" "$out" "$svg" || echo "launch: chart.py refused the run (above); the report goes on"

say "report -> $out/report.md"
python3 -I scripts/report.py "$out" | tee "$out/report.md"
[ "$st" = 0 ] || echo "launch: some hashes are not their oracles ($out/oracles.txt): a finding to read before posting"
exit "$st"
