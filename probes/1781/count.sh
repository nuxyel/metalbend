#!/usr/bin/env bash
# Counts user-mode instructions and cycles of each binary given, one thread pinned to CPU 3 (a P-core), ROUNDS times
# in alternated order; one line per run (binary, round, instructions, cycles, kernel instructions, output hash).
#   ROUNDS=3 ./count.sh build/p1781/dot-c build/p1781/dot_checked-39 ... > counts.tsv
# Wall time is recorded too, but on a busy machine it is not a number to report.
set -euo pipefail
ROUNDS=${ROUNDS:-3}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
echo -e "binary\tround\tinstructions_u\tcycles_u\tinstructions_k\tseconds\thash\tloadavg"
bins=(); for b in "$@"; do bins+=("$(realpath "$b")"); done
for r in $(seq 1 "$ROUNDS"); do
  for b in "${bins[@]}"; do
    la=$(cut -d' ' -f1 /proc/loadavg)
    t0=$(date +%s.%N)
    taskset -c 3 perf stat -x, -o "$tmp/perf" -e cpu_core/instructions/u,cpu_core/cycles/u,cpu_core/instructions/k "$b" > "$tmp/out"
    t1=$(date +%s.%N)
    ins=$(awk -F, '$3 ~ /instructions\/u/ {print $1}' "$tmp/perf")
    cyc=$(awk -F, '$3 ~ /cycles\/u/ {print $1}' "$tmp/perf")
    kin=$(awk -F, '$3 ~ /instructions\/k/ {print $1}' "$tmp/perf")
    h=$(sha256sum < "$tmp/out" | cut -c1-16)
    echo -e "$(basename "$b")\t$r\t$ins\t$cyc\t$kin\t$(awk "BEGIN{printf \"%.3f\", $t1 - $t0}")\t$h\t$la"
  done
done
