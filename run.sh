#!/usr/bin/env bash
# Builds every workload with every Bend version (and its C target, if it has one), then measures them in rounds:
#   ./run.sh                    # 5 rounds into results/<today>/
#   ROUNDS=7 VERSIONS="38 39" WORKLOADS="gemm-tile8" THREADS="1 16" ./run.sh
#   VERSIONS="39 2.1.0" BEND_2_1_0=/path/to/bend ./run.sh   # 2.0.x by its last number, later versions in full
#   GPU=1 ./run.sh              # the GPU targets too (workloads/<name>/gpu.bend, built with CUDA), into gpu.tsv
# A one-thread run is pinned to CPU 3 (a P-core) and counted by `perf stat` (instructions and cycles of the P-core PMU
# in user mode; the kernel's share, mostly page faults and transparent huge pages, varies between runs by ~1% of
# instructions and is recorded apart). A run on more threads is unpinned and measured by its wall time (its
# instructions are summed over both PMUs; its cycles are not comparable). The runtime's thread option moved between
# +RTS and -RTS in 2.0.38. Every round runs every (workload, version, threads) case once, in a fresh order from a
# seeded shuffle; the C targets run on one thread. One line per run in runs.tsv; the outputs' hashes are compared by
# analyze.py, which also writes summary.md, and then with oracles.tsv by scripts/oracle_diff.py (oracles.txt; run.sh
# exits 1 on any difference). A binary is built again when it is missing, with REBUILD=1, or when its main.bend,
# native.c, gpu.bend, a file of lib/ or its compiler is newer than it.
# GPU=1 adds each workload's GPU target, built with every version, run in the same rounds with the runtime's default
# options: its wall time, and (unless NSYS=0, or with no nsys) the time its kernels took on the device, from a second
# run under `nsys profile --trace=cuda` (its cuda_gpu_kern_sum report). One line per run in gpu.tsv, never in runs.tsv.
set -euo pipefail
cd "$(dirname "$0")"
ROUNDS=${ROUNDS:-5}
VERSIONS=${VERSIONS:-"35 36 37 38 39"}
WORKLOADS=${WORKLOADS:-$(ls workloads)}
THREADS=${THREADS:-1}
GPU=${GPU:-0}
OUT=${OUT:-results/$(date +%F)}
mkdir -p "$OUT" build
# written at the end only, so a run that stopped early leaves none (release.sh reads it)
rm -f "$OUT/oracles.txt"
# the dense-read workloads' input, made once
[ -f data/dense.bin ] || python3 -I lib/gen_dense.py
# the GPU lane, asked for: a toolkit and a device, or stop (scripts/cuda.sh)
if [ "$GPU" = 1 ]; then
  . scripts/cuda.sh
  why=$(gpu_missing)
  [ -z "$why" ] || { echo "GPU=1, but $why; stopping" >&2; exit 2; }
  if [ "${NSYS:-1}" = 1 ] && command -v nsys > /dev/null; then NSYS=1; else NSYS=0; fi
fi

# a version's name: a 2.0.x release by its last number ("39"), from 2.1 on by its full number ("2.1.0"); a name that
# is not a version ("main", a source build) is taken as it is
full() { if [[ $1 =~ ^[0-9]+$ ]]; then echo "2.0.$1"; else echo "$1"; fi; }
# where a version's compiler is: release.sh puts source builds at build/bin/<name>, and BEND_<name> (dots as
# underscores: BEND_2_1_0) names any binary; the installed releases below are where my machine keeps them, each a fixed
# copy that nothing installs over (39 is not ~/.bend/bin/bend, which the next setup.sh moves to the next pin)
bend_path() {
  if [ -x "build/bin/$1" ]; then echo "$PWD/build/bin/$1"; return; fi
  local var=BEND_${1//./_}
  if [ -n "${!var:-}" ]; then echo "${!var}"; return; fi
  case $1 in
    35) echo "$HOME/.cache/bend-2.0.35/bend" ;;
    36) echo "$HOME/.cache/bend-2.0.36/bend" ;;
    37) echo "$HOME/.bend-2.0.37/bin/bend" ;;
    38) echo "$HOME/.bend-2.0.38/bin/bend" ;;
    39) echo "$HOME/.bend-2.0.39/bin/bend" ;;
    *) return 1 ;;
  esac
}
# every version resolved once, before anything runs, and checked to report the release it names, so a binary that
# another install replaced is never measured under the old name; a name that is not a version is not checked
declare -A BENDS
for v in $VERSIONS; do
  b=$(bend_path "$v") || { echo "unknown Bend version $v (BEND_${v//./_} names its binary)" >&2; exit 2; }
  if [[ $v =~ ^[0-9]+$|^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    got=$("$b" version 2>/dev/null | awk '{print $NF}') || true
    [ "$got" = "$(full "$v")" ] || { echo "$b reports Bend ${got:-nothing}, not $(full "$v"); stopping" >&2; exit 2; }
  fi
  BENDS[$v]=$b
done
bend_of() { echo "${BENDS[$1]}"; }
# whether binary $1 must be built again: it is missing, REBUILD=1, or any of its sources ($2...) is newer than it (a
# binary left from an older main.bend, native.c, lib/ file or compiler would otherwise be measured as the new one)
stale() {
  local bin=$1 f; shift
  [ -x "$bin" ] && [ "${REBUILD:-0}" = 0 ] || return 0
  for f in "$@"; do [ "$f" -nt "$bin" ] && return 0; done
  return 1
}
# a C target's sources: its native.c, lib/'s headers and the files it includes from another workload ("../x/native.c")
c_sources() {
  echo "workloads/$1/native.c" lib/*
  sed -n 's|^#include "\.\./\([^."][^"]*\)"|workloads/\1|p' "workloads/$1/native.c"
}
# what a version's compiler was built from: a source build's wrapper (release.sh, scripts/bend_main.sh) names its tree,
# whose commit is the source; a released binary is named by its SHA-256
bend_source() {
  local wt
  wt=$(sed -n 's|^exec bun \(.*\)/bend2/main\.ts .*|\1|p' "$1" 2>/dev/null | head -1)
  if [ -n "$wt" ]; then echo "source $(git -C "$wt" rev-parse HEAD 2>/dev/null || echo unknown) ($wt)"
  else echo "binary sha256:$(sha256sum < "$(readlink -f "$1")" | cut -c1-16)"; fi
}
# the runtime's thread option ($2 threads): between +RTS and -RTS from 2.0.38 on (bendlang/bend#1530), bare before
rts() {
  if [ "$1" = c ]; then return
  elif [[ $1 =~ ^[0-9]+$ ]] && [ "$1" -lt 38 ]; then echo "--threads $2"
  else echo "+RTS --threads $2 -RTS"; fi
}

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
  echo -e "governor\t$(cat /sys/devices/system/cpu/cpu3/cpufreq/scaling_governor 2>/dev/null || echo unknown)"
  echo -e "no_turbo\t$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo unknown)"
  echo -e "thp\t$(sed 's/.*\[\(.*\)\].*/\1/' /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo unknown)"
  echo -e "bun\t$(bun --version 2>/dev/null || echo none)"
  for v in $VERSIONS; do
    echo -e "bend_$v\t$($(bend_of "$v") version)"
    echo -e "source_$v\t$(bend_source "$(bend_of "$v")")"
  done
  # the machine's state against scripts/preflight.sh's checks, and a last line `busy` naming the checks that failed
  scripts/preflight.sh --env
  # every BendHub package the corpus imports: its store id and a hash of its files
  python3 -I scripts/packages.py
  if [ "$GPU" = 1 ]; then
    echo -e "gpu\t$(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1)"
    echo -e "cuda_home\t$CUDA_HOME ($(ls "$CUDA_LIB"/libnvrtc.so.* 2>/dev/null | sed 's|.*/||' | sort | tail -1))"
    echo -e "nsys\t$([ "$NSYS" = 1 ] && nsys --version | head -1 || echo none)"
  fi
} > "$OUT/env.tsv"

# ---- builds: one binary per (workload, version); a failure is recorded, not fixed ----
[ -f "$OUT/builds.tsv" ] || echo -e "workload\tbend\tstatus\tseconds" > "$OUT/builds.tsv"
for w in $WORKLOADS; do
  for v in $VERSIONS; do
    bin=build/$v/$w
    mkdir -p "build/$v"
    # resolved here, not inside the subshell: after its cd, a relative path would miss
    bend=$(bend_of "$v")
    stale "$bin" "workloads/$w/main.bend" lib/* "$(readlink -f "$bend")" || continue
    t0=$(date +%s.%N)
    if (cd "workloads/$w" && "$bend" main.bend -o "../../$bin") > "build/$v/$w.log" 2>&1; then st=ok; else st=fail; rm -f "$bin"; fi
    t1=$(date +%s.%N)
    echo -e "$w\t$v\t$st\t$(awk "BEGIN{printf \"%.2f\", $t1 - $t0}")" | tee -a "$OUT/builds.tsv"
  done
done

# ---- the C targets: native.c next to a workload's main.bend, built with the flags `bend -o` gives clang ----
for w in $WORKLOADS; do
  [ -f "workloads/$w/native.c" ] || continue
  mkdir -p build/c
  # shellcheck disable=SC2046
  stale "build/c/$w" $(c_sources "$w") || continue
  if clang -std=c11 -O3 "workloads/$w/native.c" -o "build/c/$w" -lm > "build/c/$w.log" 2>&1; then st=ok; else st=fail; fi
  echo -e "$w\tc\t$st\t0" | tee -a "$OUT/builds.tsv"
done

# ---- the GPU targets: gpu.bend next to a main.bend, built with CUDA by each version (a CPU-only build is a failure) ----
if [ "$GPU" = 1 ]; then
  for w in $WORKLOADS; do
    [ -f "workloads/$w/gpu.bend" ] || continue
    for v in $VERSIONS; do
      bin=build/gpu-$v/$w
      mkdir -p "build/gpu-$v"
      bend=$(bend_of "$v")
      stale "$bin" "workloads/$w/gpu.bend" lib/* "$(readlink -f "$bend")" || continue
      t0=$(date +%s.%N)
      if gpu_build "$w" "$bend" "$PWD/$bin" > "build/gpu-$v/$w.log" 2>&1; then st=ok; else st=fail; rm -f "$bin"; fi
      t1=$(date +%s.%N)
      echo -e "$w\tgpu-$v\t$st\t$(awk "BEGIN{printf \"%.2f\", $t1 - $t0}")" | tee -a "$OUT/builds.tsv"
    done
  done
  [ -f "$OUT/gpu.tsv" ] || echo -e "round\tworkload\tbend\tseconds\tkernel_ms\tkernels\thash\tstatus\tloadavg" > "$OUT/gpu.tsv"
fi

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
      # the process may end between the two lines: ls then fails, which under pipefail would end run.sh silently
      n=$(ls "/proc/$pid/task" 2>/dev/null | wc -l) || n=0
      [ "$n" -gt "$peak" ] && peak=$n
      sleep 0.02
    done
    wait "$pid" || true
    echo -e "$v\t$t\t$peak" >> "$OUT/threads.tsv"
    if [ "$t" = 1 ]; then ok=$([ "$peak" = 1 ] && echo y || echo n); else ok=$([ "$peak" -ge "$t" ] && [ "$peak" -le $((t + 2)) ] && echo y || echo n); fi
    [ "$ok" = y ] || { echo "Bend $(full "$v") ran on $peak threads with the option for $t; stopping" >&2; exit 1; }
  done
done

# ---- rounds ----
[ -f "$OUT/runs.tsv" ] || echo -e "round\tworkload\tbend\tinstructions\tcycles\tkinstructions\tkcycles\tseconds\thash\tstatus\tloadavg\tthreads" > "$OUT/runs.tsv"
pairs=()
for w in $WORKLOADS; do
  for v in $VERSIONS; do for t in $THREADS; do [ -x "build/$v/$w" ] && pairs+=("$w:$v:$t"); done; done
  [ -x "build/c/$w" ] && pairs+=("$w:c:1")
  if [ "$GPU" = 1 ]; then for v in $VERSIONS; do [ -x "build/gpu-$v/$w" ] && pairs+=("$w:$v:gpu"); done; fi
done
# nothing built: no rounds (an empty pairs would still feed one empty case to the shuffle)
[ "${#pairs[@]}" -gt 0 ] || ROUNDS=0
for r in $(seq 1 "$ROUNDS"); do
  mapfile -t order < <(printf '%s\n' "${pairs[@]}" | python3 -I -c "import random,sys; l=sys.stdin.read().split(); random.Random($r).shuffle(l); print('\n'.join(l))")
  for p in "${order[@]}"; do
    IFS=: read -r w v t <<< "$p"
    la=$(cut -d' ' -f1 /proc/loadavg)
    if [ "$t" = gpu ]; then
      bin=build/gpu-$v/$w
      t0=$(date +%s.%N)
      if "$bin" > "$OUT/.out" 2> "$OUT/.err"; then st=ok; else st="exit$?"; fi
      t1=$(date +%s.%N)
      h=$(sha256sum < "$OUT/.out" | cut -c1-16)
      kms="" nk=""
      if [ "$NSYS" = 1 ] && nsys profile --trace=cuda --output "$OUT/.nsys" --force-overwrite true "$bin" > /dev/null 2>&1; then
        read -r kms nk < <(nsys stats -q --report cuda_gpu_kern_sum --format csv --output - --force-export true "$OUT/.nsys.nsys-rep" 2>/dev/null |
          awk -F, 'go {ns += $2; n += $3} /^Time \(%\)/ {go = 1} END {if (go) printf "%.3f %d\n", ns / 1e6, n}') || true
      fi
      rm -f "$OUT/.nsys.nsys-rep" "$OUT/.nsys.sqlite"
      echo -e "$r\t$w\t$v\t$(awk "BEGIN{printf \"%.4f\", $t1 - $t0}")\t$kms\t$nk\t$h\t$st\t$la" | tee -a "$OUT/gpu.tsv"
      [ -f "$OUT/out-$w-$v-gpu.txt" ] || cp "$OUT/.out" "$OUT/out-$w-$v-gpu.txt"
      continue
    fi
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
python3 -I analyze.py "$OUT" "${ORACLES:-oracles.tsv}"
# every case against oracles.tsv ($ORACLES): a differing hash, a failed run, a missing build; run.sh exits 1 on any
python3 -I scripts/oracle_diff.py "$OUT" "${ORACLES:-oracles.tsv}" | tee "$OUT/oracles.txt"
exit "${PIPESTATUS[0]}"
