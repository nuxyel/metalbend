#!/usr/bin/env bash
# The history's cycles: the corpus on Bend 2.0.32, 2.0.33 and 2.0.34 under perf on an idle machine, with 2.0.35 in the
# same rounds to tie them to the runs results/ already has from 2.0.35 on (Cachegrind's counts of every release are
# history.yml's, on GitHub's runners). Each old release is built from its tag (scripts/bend_main.sh, into
# build/bin/<n>, where run.sh looks first), then run.sh measures every workload at 1 and 16 threads, 5 rounds, into
# results/<date>-2.0.32-2.0.34/. read-bf16 and read-binary do not build before 2.0.36: run.sh records the failed builds
# and goes on. No GPU lane. On an idle machine only, through scripts/when_idle.sh (the command is in NOTES.md,
# 2026-11-07); ROUNDS, THREADS and OUT as run.sh's.
#   scripts/history_cycles.sh
set -euo pipefail
cd "$(dirname "$0")/.."
OLD=${OLD:-"32 33 34"}
OUT=${OUT:-results/$(date +%F)-2.0.32-2.0.34}
for n in $OLD; do
  BIN=build/bin/$n scripts/bend_main.sh "v2.0.$n"
done
st=0
OUT=$OUT VERSIONS="$OLD 35" THREADS=${THREADS:-"1 16"} ROUNDS=${ROUNDS:-5} ./run.sh > "build/history_cycles.log" 2>&1 || st=$?
[ -f "$OUT/oracles.txt" ] || { echo "run.sh stopped (exit $st) before the end; build/history_cycles.log" >&2; exit "$st"; }
echo "== $OUT/summary.md"
sed -n '/## Beyond noise or differing outputs/,$p' "$OUT/summary.md"
echo "== against oracles.tsv"
cat "$OUT/oracles.txt"
exit "$st"
