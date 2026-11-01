#!/usr/bin/env bash
# Whether this machine is fit for timings, before a run that measures them (CLAUDE.md's rule 3):
#   scripts/preflight.sh          # one line per check (check, value, ok or busy); exits 1 if any is busy
#   scripts/preflight.sh --env    # the same as key/value lines for env.tsv (run.sh), and a last line `busy`; exits 0
# The checks: mains power; the power profile `performance`; the one-minute load average under MAX_LOAD (1.0); no
# other Bend compiler or agent running (bend, a source build's bend2/main.ts, opencode, claude, codex); perf_event_paranoid
# at most 1 (run.sh counts kernel-mode events too); and CPU 3's SMT sibling idle over PREFLIGHT_SAMPLE seconds (1), under 10%
# of its time busy, since run.sh pins one thread to CPU 3 and the sibling shares its core.
# Only timings need this: the bits (make check) and instruction counts on a busy machine are labeled, never refused.
# PREFLIGHT_SYS and PREFLIGHT_PROC (/sys and /proc) are for the tests.
set -uo pipefail
SYS=${PREFLIGHT_SYS:-/sys}
PROC=${PREFLIGHT_PROC:-/proc}
MAX_LOAD=${MAX_LOAD:-1.0}
SAMPLE=${PREFLIGHT_SAMPLE:-1}
mode=${1:-table}

rows=()
check() { rows+=("$1"$'\t'"$2"$'\t'"$3"); }

# mains power: a Mains supply online; a machine with no battery is on mains by construction
ac=unknown battery=0
for s in "$SYS"/class/power_supply/*; do
  [ -f "$s/type" ] || continue
  case $(cat "$s/type") in
    Mains) [ "$(cat "$s/online" 2>/dev/null)" = 1 ] && ac=online || { [ "$ac" = online ] || ac=offline; } ;;
    Battery) battery=1 ;;
  esac
done
[ "$ac" = unknown ] && [ "$battery" = 0 ] && ac="no battery"
check ac "$ac" "$([ "$ac" = online ] || [ "$ac" = "no battery" ] && echo ok || echo busy)"

profile=$(powerprofilesctl get 2>/dev/null || echo unknown)
check power_profile "$profile" "$([ "$profile" = performance ] && echo ok || echo busy)"

load=$(cut -d' ' -f1 "$PROC/loadavg")
check loadavg "$load" "$(awk -v l="$load" -v m="$MAX_LOAD" 'BEGIN {print (l < m) ? "ok" : "busy"}')"

# other compilers and agents, by command name (a source build of Bend is bun running bend2/main.ts)
others=$(ps -eo pid=,comm=,args= 2>/dev/null | awk -v self=$$ '
  $1 == self {next}
  $2 ~ /^(bend|claude|codex.*|opencode.*)$/ || $0 ~ /bend2\/main\.ts/ {n[$2]++}
  END {for (c in n) printf "%s%s x%d", (s++ ? ", " : ""), c, n[c]}')
check other_processes "${others:-none}" "$([ -z "$others" ] && echo ok || echo busy)"

paranoid=$(cat "$PROC/sys/kernel/perf_event_paranoid" 2>/dev/null || echo unknown)
check perf_event_paranoid "$paranoid" "$([[ $paranoid =~ ^-?[0-9]+$ ]] && [ "$paranoid" -le 1 ] && echo ok || echo busy)"

# CPU 3's SMT siblings (thread_siblings_list, as "2-3" or "2,3"), each sampled from /proc/stat
siblings=$(tr ',' '\n' < "$SYS/devices/system/cpu/cpu3/topology/thread_siblings_list" 2>/dev/null |
  awk -F- '{for (c = $1; c <= ($2 == "" ? $1 : $2); c++) if (c != 3) print c}')
if [ -z "$siblings" ]; then
  check cpu3_sibling none ok
else
  stat() { awk -v c="cpu$1" '$1 == c {print $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9, $5 + $6}' "$PROC/stat"; }
  declare -A t0 i0
  for c in $siblings; do read -r t0[$c] i0[$c] < <(stat "$c"); done
  sleep "$SAMPLE"
  for c in $siblings; do
    read -r t1 i1 < <(stat "$c")
    busy=$(awk -v dt=$((t1 - t0[$c])) -v di=$((i1 - i0[$c])) 'BEGIN {printf "%.0f", dt ? 100 * (dt - di) / dt : 0}')
    check cpu3_sibling "cpu$c ${busy}%" "$([ "$busy" -lt 10 ] && echo ok || echo busy)"
  done
fi

busy=$(printf '%s\n' "${rows[@]}" | awk -F'\t' '$3 == "busy" {printf "%s%s", (n++ ? "," : ""), $1}')
if [ "$mode" = --env ]; then
  printf '%s\n' "${rows[@]}" | awk -F'\t' '{print "pre_" $1 "\t" $2}'
  echo -e "busy\t${busy:-no}"
  exit 0
fi
printf '%s\n' "${rows[@]}" | awk -F'\t' '{printf "%-6s %-20s %s\n", $3, $1, $2}'
if [ -n "$busy" ]; then echo "preflight: busy ($busy): timings from this machine now are not results"; exit 1; fi
echo "preflight: idle, fit for timings"
