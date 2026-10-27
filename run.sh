#!/usr/bin/env bash
# Builds every workload with every Bend version (and its C target, if it has one), then measures them in rounds:
#   ./run.sh                    # 5 rounds into results/<today>/
#   ROUNDS=7 VERSIONS="38 39" WORKLOADS="gemm-tile8" THREADS="1 16" ./run.sh
# A one-thread run is pinned to CPU 3 (a P-core) and counted by `perf stat` (instructions and cycles of the P-core PMU
# in user mode; the kernel's share, mostly page faults and transparent huge pages, varies between runs by ~1% of
# instructions and is recorded apart). A run on more threads is unpinned and measured by its wall time (its
# instructions are summed over both PMUs; its cycles are not comparable). The runtime's thread option moved between
# +RTS and -RTS in 2.0.38. Every round runs every (workload, version, threads) case once, in a fresh order from a
# seeded shuffle; the C targets run on one thread. One line per run in runs.tsv; the output's hash is the oracle, compared by
# analyze.py, which also writes summary.md.
set -euo pipefail
cd "$(dirname "$0")"
ROUNDS=${ROUNDS:-5}
VERSIONS=${VERSIONS:-"35 36 37 38 39"}
WORKLOADS=${WORKLOADS:-$(ls workloads)}
THREADS=${THREADS:-1}
OUT=${OUT:-results/$(date +%F)}
mkdir -p "$OUT" build
# the dense-read workloads' input, made once
[ -f data/dense.bin ] || python3 -I lib/gen_dense.py

# a version is its last number; release.sh puts source builds of new ones at build/bin/<n>, and BEND_<n> names an
# installed binary (BEND_39=~/.bend/bin/bend); the paths below are where my machine keeps them
bend_of() {
  if [ -x "build/bin/$1" ]; then echo "$PWD/build/bin/$1"; return; fi
  local var=BEND_$1
  if [ -n "${!var:-}" ]; then echo "${!var}"; return; fi
  case $1 in
    35) echo "$HOME/.cache/bend-2.0.35/bend" ;;
    36) echo "$HOME/.cache/bend-2.0.36/bend" ;;
    37) echo "$HOME/.bend-2.0.37/bin/bend" ;;
    38) echo "$HOME/.bend-2.0.38/bin/bend" ;;
    39) echo "$HOME/.bend/bin/bend" ;;
    *) echo "unknown Bend version $1" >&2; exit 2 ;;
  esac
}
# the runtime's thread option ($2 threads): between +RTS and -RTS from 2.0.38 on (bendlang/bend#1530), bare before
rts() { if [ "$1" = c ]; then return; elif [ "$1" -ge 38 ]; then echo "+RTS --threads $2 -RTS"; else echo "--threads $2"; fi; }

# ---- the machine, recorded before anything runs ----
{
  echo -e "key\tvalue"
  echo -e "date\t$(date -Is)"
  echo -e "cpu\t$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | sed 's/^ //')"
  echo -e "kernel\t$(uname -r)"
  echo -e "clang\t$(clang --version | head -1)"
  echo -e "ac_online\t$(cat /sys/class/power_supply/ADP1/online 2>/dev/null || echo unknown)"
  echo -e "power_profile\t$(powerprofilesctl get 2>/dev/null || echo unknown)"
  echo -e "loadavg_start\t$(cut -d' ' -f1-3 /proc/loadavg)"
  echo -e "metalbend\t$(git rev-parse --short HEAD)$(git diff --quiet || echo -dirty)"
  for v in $VERSIONS; do echo -e "bend_$v\t$($(bend_of "$v") version)"; done
} > "$OUT/env.tsv"

# ---- builds: one binary per (workload, version); a failure is recorded, not fixed ----
[ -f "$OUT/builds.tsv" ] || echo -e "workload\tbend\tstatus\tseconds" > "$OUT/builds.tsv"
for w in $WORKLOADS; do
  for v in $VERSIONS; do
    bin=build/$v/$w
    mkdir -p "build/$v"
    if [ -x "$bin" ] && [ "${REBUILD:-0}" = 0 ]; then continue; fi
    t0=$(date +%s.%N)
    if (cd "workloads/$w" && "$(bend_of "$v")" main.bend -o "../../$bin") > "build/$v/$w.log" 2>&1; then st=ok; else st=fail; rm -f "$bin"; fi
    t1=$(date +%s.%N)
    echo -e "$w\t$v\t$st\t$(awk "BEGIN{printf \"%.2f\", $t1 - $t0}")" | tee -a "$OUT/builds.tsv"
  done
done

# ---- the C targets: native.c next to a workload's main.bend, built with the flags `bend -o` gives clang ----
for w in $WORKLOADS; do
  [ -f "workloads/$w/native.c" ] || continue
  mkdir -p build/c
  if [ -x "build/c/$w" ] && [ "${REBUILD:-0}" = 0 ]; then continue; fi
  if clang -std=c11 -O3 "workloads/$w/native.c" -o "build/c/$w" -lm > "build/c/$w.log" 2>&1; then st=ok; else st=fail; fi
  echo -e "$w\tc\t$st\t0" | tee -a "$OUT/builds.tsv"
done

# ---- guard: the thread option is honored (a bare option on 2.0.38+ would run on every core, silently): the peak
# count of the process's threads is 1 for one thread, and t to t + 2 for t (the runtime may add a helper) ----
[ -f "$OUT/threads.tsv" ] || echo -e "bend\tthreads\tthreads_peak" > "$OUT/threads.tsv"
for v in $VERSIONS; do
  for t in $THREADS; do
    bin=build/$v/block-step
    [ -x "$bin" ] || continue
    # shellcheck disable=SC2046
    "$bin" $(rts "$v" "$t") > /dev/null & pid=$!
    peak=0
    while kill -0 "$pid" 2>/dev/null; do
      n=$(ls "/proc/$pid/task" 2>/dev/null | wc -l)
      [ "$n" -gt "$peak" ] && peak=$n
      sleep 0.02
    done
    wait "$pid" || true
    echo -e "$v\t$t\t$peak" >> "$OUT/threads.tsv"
    if [ "$t" = 1 ]; then ok=$([ "$peak" = 1 ] && echo y || echo n); else ok=$([ "$peak" -ge "$t" ] && [ "$peak" -le $((t + 2)) ] && echo y || echo n); fi
    [ "$ok" = y ] || { echo "Bend 2.0.$v ran on $peak threads with the option for $t; stopping" >&2; exit 1; }
  done
done

# ---- rounds ----
[ -f "$OUT/runs.tsv" ] || echo -e "round\tworkload\tbend\tinstructions\tcycles\tkinstructions\tkcycles\tseconds\thash\tstatus\tloadavg\tthreads" > "$OUT/runs.tsv"
pairs=()
for w in $WORKLOADS; do
  for v in $VERSIONS; do for t in $THREADS; do [ -x "build/$v/$w" ] && pairs+=("$w:$v:$t"); done; done
  [ -x "build/c/$w" ] && pairs+=("$w:c:1")
done
for r in $(seq 1 "$ROUNDS"); do
  mapfile -t order < <(printf '%s\n' "${pairs[@]}" | python3 -I -c "import random,sys; l=sys.stdin.read().split(); random.Random($r).shuffle(l); print('\n'.join(l))")
  for p in "${order[@]}"; do
    IFS=: read -r w v t <<< "$p"
    la=$(cut -d' ' -f1 /proc/loadavg)
    if [ "$t" = 1 ]; then pin="taskset -c 3"; ev=cpu_core/instructions/u,cpu_core/cycles/u,cpu_core/instructions/k,cpu_core/cycles/k
    else pin=""; ev=cpu_core/instructions/u,cpu_atom/instructions/u,cpu_core/cycles/u,cpu_core/instructions/k,cpu_core/cycles/k; fi
    t0=$(date +%s.%N)
    # shellcheck disable=SC2046,SC2086
    if $pin perf stat -x, -o "$OUT/.perf" -e $ev "build/$v/$w" $(rts "$v" "$t") > "$OUT/.out" 2> "$OUT/.err"; then st=ok; else st="exit$?"; fi
    t1=$(date +%s.%N)
    ins=$(awk -F, '$3 ~ /instructions\/u/ && $1 ~ /^[0-9]+$/ {s += $1} END {print s}' "$OUT/.perf")
    cyc=$(awk -F, '$3 ~ /cpu_core\/cycles\/u/{print $1}' "$OUT/.perf")
    kins=$(awk -F, '$3 ~ /instructions\/k/{print $1}' "$OUT/.perf")
    kcyc=$(awk -F, '$3 ~ /cycles\/k/{print $1}' "$OUT/.perf")
    h=$(sha256sum < "$OUT/.out" | cut -c1-16)
    echo -e "$r\t$w\t$v\t$ins\t$cyc\t$kins\t$kcyc\t$(awk "BEGIN{printf \"%.4f\", $t1 - $t0}")\t$h\t$st\t$la\t$t" | tee -a "$OUT/runs.tsv"
    # the full output of the first run of each case, for reading what a differing hash means
    [ -f "$OUT/out-$w-$v-t$t.txt" ] || cp "$OUT/.out" "$OUT/out-$w-$v-t$t.txt"
  done
done
rm -f "$OUT/.perf" "$OUT/.out" "$OUT/.err"
echo -e "loadavg_end\t$(cut -d' ' -f1-3 /proc/loadavg)" >> "$OUT/env.tsv"
python3 -I analyze.py "$OUT"
