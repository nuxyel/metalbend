#!/usr/bin/env bash
# The bits check: builds every workload with the pinned Bend and every C target with clang, runs them, and fails when
# a hash differs from oracles.tsv's. No timings: it runs anywhere, CI's runners included.
#   scripts/check_oracles.sh                         # every workload, Bend on 1 and 16 threads, every native.c
#   WORKLOADS="softmax-ce" THREADS=1 scripts/check_oracles.sh
#   TARGETS=c scripts/check_oracles.sh                # the C targets only (TARGETS="bend c" by default)
#   TARGETS=gpu scripts/check_oracles.sh              # the GPU targets only (make check-gpu): local, CI has no GPU
# The hash is run.sh's: the first 16 hex digits of the SHA-256 of the program's whole stdout. Every workload needs a
# line in oracles.tsv, and every line there a workload; a native.c next to a main.bend is picked up by itself and must
# print the same hash. A gpu.bend next to a main.bend is its GPU target (target gpu, never in the default
# TARGETS): built with CUDA (scripts/cuda.sh), it must print the oracle of line <name>:gpu on the device, and <name>'s
# own oracle on the CPU threads (+RTS --gpu off), on each thread count; with no toolkit or no GPU it is skipped with the
# reason, not failed. BEND names the compiler (bend on PATH by default), which must be Bend $PIN unless ANY_BEND=1.
# Builds go to $OUT (build/check by default), fresh on every call.
set -uo pipefail
cd "$(dirname "$0")/.."
PIN=2.0.40
BEND=${BEND:-bend}
# a path (build/bin/main) made absolute: the builds run from inside each workload's folder
case $BEND in */*) BEND=$(realpath "$BEND") ;; esac
WORKLOADS=${WORKLOADS:-$(ls workloads)}
THREADS=${THREADS:-"1 16"}
TARGETS=${TARGETS:-"bend c"}
OUT=${OUT:-build/check}
export BEND_NO_TELEMETRY=1

fail=0
bad() { echo "FAIL $*"; fail=1; }
has() { [[ " $TARGETS " == *" $1 "* ]]; }

declare -A want
while IFS=$'\t' read -r w h; do
  [ "$w" = workload ] && continue
  [ -n "$w" ] && want[$w]=$h
done < oracles.tsv
for w in "${!want[@]}"; do
  case $w in
    *:gpu) [ -f "workloads/${w%:gpu}/gpu.bend" ] || bad "oracles.tsv names $w, which has no workloads/${w%:gpu}/gpu.bend" ;;
    *) [ -f "workloads/$w/main.bend" ] || bad "oracles.tsv names $w, which has no workloads/$w/main.bend" ;;
  esac
done

if has gpu; then
  . scripts/cuda.sh
  why=$(gpu_missing)
  if [ -n "$why" ]; then echo "skip the GPU targets: $why"; TARGETS=${TARGETS//gpu/}; fi
  [ -n "${TARGETS// /}" ] || { [ "$fail" = 0 ] && echo "check: nothing else to run"; exit "$fail"; }
fi
if has bend || has gpu; then
  got=$("$BEND" version 2>/dev/null | awk '{print $NF}')
  [ "$got" = "$PIN" ] || [ "${ANY_BEND:-0}" = 1 ] || { echo "$BEND is Bend ${got:-?}, not $PIN (ANY_BEND=1 to run it anyway)"; exit 2; }
fi
# the dense-read workloads' input, deterministic (lib/gen_dense.py)
[ -f data/dense.bin ] || python3 -I lib/gen_dense.py
# read-bf16's safetensors file (lib/gen_bf16.py)
[ ! -d workloads/read-bf16 ] || [ -f data/bf16.safetensors ] || python3 -I lib/gen_bf16.py

rm -rf "$OUT"
mkdir -p "$OUT"
OUT=$(cd "$OUT" && pwd)
# runs a binary ($2...) and compares its output's hash with workload $1's oracle; the label is $LABEL
run() {
  local w=$1; shift
  local h st
  "$@" > "$OUT/.out" 2> "$OUT/.err"; st=$?
  h=$(sha256sum < "$OUT/.out" | cut -c1-16)
  if [ "$st" != 0 ]; then bad "$LABEL: exit $st ($(tail -c 300 "$OUT/.err" | tr '\n' ' '))"
  elif [ "$h" != "${want[$w]}" ]; then bad "$LABEL: hash $h, oracle ${want[$w]}"
  else echo "ok   $LABEL: $h"; fi
}

n=0
for w in $WORKLOADS; do
  [ -f "workloads/$w/main.bend" ] || { bad "$w: no workloads/$w/main.bend"; continue; }
  [ -n "${want[$w]:-}" ] || { bad "$w: no oracle (add its line to oracles.tsv)"; continue; }
  if has bend; then
    if (cd "workloads/$w" && "$BEND" main.bend -o "$OUT/$w") > "$OUT/$w.log" 2>&1; then
      for t in $THREADS; do LABEL="$w, Bend $PIN, $t thread$([ "$t" = 1 ] || echo s)" run "$w" "$OUT/$w" +RTS --threads "$t" -RTS; n=$((n + 1)); done
    else
      bad "$w: Bend build failed ($(tail -c 300 "$OUT/$w.log" | tr '\n' ' '))"
    fi
  fi
  if has c && [ -f "workloads/$w/native.c" ]; then
    # the flags `bend -o` gives clang
    if clang -std=c11 -O3 "workloads/$w/native.c" -o "$OUT/$w.c" -lm > "$OUT/$w.c.log" 2>&1; then
      LABEL="$w, C target" run "$w" "$OUT/$w.c"; n=$((n + 1))
    else
      bad "$w: C build failed ($(tail -c 300 "$OUT/$w.c.log" | tr '\n' ' '))"
    fi
  fi
  if has gpu && [ -f "workloads/$w/gpu.bend" ]; then
    if [ -z "${want[$w:gpu]:-}" ]; then bad "$w: a gpu.bend and no oracle $w:gpu (add its line to oracles.tsv)"
    elif gpu_build "$w" "$BEND" "$OUT/$w.gpu" > "$OUT/$w.gpu.log" 2>&1; then
      LABEL="$w, GPU target, on the GPU" run "$w:gpu" "$OUT/$w.gpu"; n=$((n + 1))
      for t in $THREADS; do
        LABEL="$w, GPU target, --gpu off, $t thread$([ "$t" = 1 ] || echo s)" run "$w" "$OUT/$w.gpu" +RTS --gpu off --threads "$t" -RTS
        n=$((n + 1))
      done
    else
      bad "$w: GPU build failed or links no libnvrtc ($(tail -c 300 "$OUT/$w.gpu.log" | tr '\n' ' '))"
    fi
  fi
done
rm -f "$OUT/.out" "$OUT/.err"
if [ "$fail" = 0 ]; then echo "check: $n runs, every hash is its oracle"; else echo "check: FAILED"; fi
exit "$fail"
