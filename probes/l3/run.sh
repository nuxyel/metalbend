#!/usr/bin/env bash
# Counts each binary given on CPU 3 (`taskset -c 3`; CPU=<n> picks another, scripts/pmu.sh), with and without the
# antagonist: one `stream` per E-core (other than CPU) that shares the P-cores' L3 (from sysfs: cpu_atom's CPUs that
# have an index3 cache), each streaming its own BUF_MB (64) MB; STREAMS=<n> uses only the first n of them. ROUNDS (5)
# rounds; round r runs `idle` then `busy` when r is odd and the other way when even, and each condition runs the
# binaries in an order shuffled with the round as seed. One line per run:
#   ROUNDS=5 probes/l3/run.sh $(probes/l3/build.sh) > probes/l3/results/<date>.tsv
# Columns: round, cond, binary, instructions_u, cycles_u, l3_miss_u (mem_load_retired.l3_miss, of the pinned CPU's
# PMU), seconds, hash (first 16 hex of the output's SHA-256), loadavg (one minute, before the run), stream_gbs (the
# antagonists' summed rate over the condition's runs, the same on each of its lines; empty when idle).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
# CPU and its PMU (cpu_core on a hybrid Intel CPU, plain cpu elsewhere)
. "$root/scripts/pmu.sh"
ROUNDS=${ROUNDS:-5}
BUF_MB=${BUF_MB:-64}
WARMUP=${WARMUP:-2}
stream=$root/build/l3/stream
[ -x "$stream" ] || { echo "no $stream: run probes/l3/build.sh first" >&2; exit 1; }
[ $# -gt 0 ] || { echo "usage: probes/l3/run.sh <binary>..." >&2; exit 1; }
ecores=()
for c in $(tr ',' '\n' < /sys/devices/cpu_atom/cpus 2>/dev/null | awk -F- '{for (i = $1; i <= ($2 == "" ? $1 : $2); i++) print i}'); do
  [ "$c" != "$CPU" ] && [ -d "/sys/devices/system/cpu/cpu$c/cache/index3" ] && ecores+=("$c")
done
[ ${#ecores[@]} -gt 0 ] || { echo "no E-core shares the L3 here" >&2; exit 1; }
ecores=("${ecores[@]:0:${STREAMS:-${#ecores[@]}}}")
echo "antagonist on CPUs ${ecores[*]}, ${BUF_MB} MB each" >&2
tmp=$(mktemp -d)
pids=()
stop_stream() {
  [ ${#pids[@]} -gt 0 ] || return 0
  kill -TERM "${pids[@]}" 2>/dev/null || true
  wait "${pids[@]}" 2>/dev/null || true
  pids=()
}
trap 'stop_stream; rm -rf "$tmp"' EXIT
bins=(); for b in "$@"; do bins+=("$(realpath "$b")"); done
ev=$PMU_ONE/instructions/u,$PMU_ONE/cycles/u,$PMU_ONE/mem_load_retired.l3_miss/u
echo -e "round\tcond\tbinary\tinstructions_u\tcycles_u\tl3_miss_u\tseconds\thash\tloadavg\tstream_gbs"
for r in $(seq 1 "$ROUNDS"); do
  if [ $((r % 2)) = 1 ]; then conds="idle busy"; else conds="busy idle"; fi
  for cond in $conds; do
    if [ "$cond" = busy ]; then
      rm -f "$tmp"/gbs.*
      for c in "${ecores[@]}"; do
        BUF_MB=$BUF_MB taskset -c "$c" "$stream" 2> "$tmp/gbs.$c" &
        pids+=($!)
      done
      sleep "$WARMUP"
    fi
    lines=()
    for b in $(printf '%s\n' "${bins[@]}" | python3 -I -c "import random,sys; l=sys.stdin.read().split(); random.Random($r).shuffle(l); print('\n'.join(l))"); do
      la=$(cut -d' ' -f1 /proc/loadavg)
      t0=$(date +%s.%N)
      taskset -c "$CPU" perf stat -x, -o "$tmp/perf" -e "$ev" "$b" > "$tmp/out"
      t1=$(date +%s.%N)
      ins=$(awk -F, '$3 ~ /instructions\/u/ {print $1}' "$tmp/perf")
      cyc=$(awk -F, '$3 ~ /cycles\/u/ {print $1}' "$tmp/perf")
      l3=$(awk -F, '$3 ~ /l3_miss\/u/ {print $1}' "$tmp/perf")
      h=$(sha256sum < "$tmp/out" | cut -c1-16)
      lines+=("$r"$'\t'"$cond"$'\t'"$(basename "$b")"$'\t'"$ins"$'\t'"$cyc"$'\t'"$l3"$'\t'"$(awk "BEGIN{printf \"%.3f\", $t1 - $t0}")"$'\t'"$h"$'\t'"$la")
    done
    gbs=
    if [ "$cond" = busy ]; then
      stop_stream
      gbs=$(cat "$tmp"/gbs.* | awk '{s += $1} END {printf "%.1f", s}')
    fi
    for l in "${lines[@]}"; do echo -e "$l\t$gbs"; done
  done
done
