#!/usr/bin/env bash
# Whether this machine is fit for timings, before a run that measures them (CLAUDE.md's rule 3):
#   scripts/preflight.sh          # one line per check (check, value, ok or busy); exits 1 if any is busy
#   scripts/preflight.sh --env    # the same as key/value lines for env.tsv (run.sh), and a last line `busy`; exits 0
# The checks: the one-minute load average under MAX_LOAD (2.0; the runs of record started at 0.9-1.4), read first so
# the other checks' processes do not count in it; mains power; the power profile `performance`; no other Bend compiler
# or agent running (bend, a source build's bend2/main.ts, opencode, claude, codex; with AGENTS_IDLE_OK=1 an agent whose
# process tree is idle passes, below); perf_event_paranoid at most 1
# (run.sh counts kernel-mode events too); and the SMT sibling of CPU (3, as in run.sh) idle over PREFLIGHT_SAMPLE
# seconds (1), under 10% of its time busy, since run.sh pins one thread to that CPU and the sibling shares its core.
# The check is named after the CPU (cpu3_sibling).
# Only timings need this: the bits (make check) and instruction counts on a busy machine are labeled, never refused.
# PREFLIGHT_SYS and PREFLIGHT_PROC (/sys and /proc) are for the tests.
set -uo pipefail
SYS=${PREFLIGHT_SYS:-/sys}
PROC=${PREFLIGHT_PROC:-/proc}
MAX_LOAD=${MAX_LOAD:-2.0}
SAMPLE=${PREFLIGHT_SAMPLE:-1}
CPU=${CPU:-3}
mode=${1:-table}

rows=()
check() { rows+=("$1"$'\t'"$2"$'\t'"$3"); }

# the load average first, before this script's own processes (powerprofilesctl, ps, the sibling's sample) add to it
load=$(cut -d' ' -f1 "$PROC/loadavg")
check loadavg "$load" "$(awk -v l="$load" -v m="$MAX_LOAD" 'BEGIN {print (l < m) ? "ok" : "busy"}')"

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

# other compilers and agents, by command name (a source build of Bend is bun running bend2/main.ts)
plist=$(ps -eo pid=,comm=,args= 2>/dev/null)
others=$(awk -v self=$$ '
  $1 == self {next}
  $2 ~ /^(bend|claude|codex.*|opencode.*)$/ || $0 ~ /bend2\/main\.ts/ {n[$2]++}
  END {for (c in n) printf "%s%s x%d", (s++ ? ", " : ""), c, n[c]}' <<< "$plist")
# AGENTS_IDLE_OK=1 (Renan, 2026-11-06): an agent session left open and idle does not make the machine busy. Its whole
# process tree (every descendant, so a build it runs counts) must use under AGENT_MAX_PCT percent of one CPU (2) over
# AGENT_SAMPLE seconds (SAMPLE), from utime + stime in $PROC/<pid>/stat. A Bend compiler still makes it busy.
agents_idle() {  # prints "idle <pct>%" and succeeds, or prints "<pct>%" and fails
  local pids ticks0 ticks1 tck pct
  pids=$(awk '$2 ~ /^(claude|codex.*|opencode.*)$/ {print $1}' <<< "$plist")
  [ -n "$pids" ] || return 1
  tree_ticks() {  # utime + stime of the agents and every descendant, in clock ticks
    awk -v roots="$pids" '
      FNR == 1 { s = $0; sub(/^.*\) /, "", s); split(s, f, " "); p = FILENAME; sub(/\/stat$/, "", p); sub(/^.*\//, "", p)
                 ppid[p] = f[2]; t[p] = f[12] + f[13] }
      END { n = split(roots, r, " "); for (i = 1; i <= n; i++) in_tree[r[i]] = 1
            do { grew = 0; for (p in ppid) if (!(p in in_tree) && (ppid[p] in in_tree)) { in_tree[p] = 1; grew = 1 } } while (grew)
            for (p in in_tree) sum += t[p]; print sum + 0 }' "$PROC"/[0-9]*/stat 2>/dev/null
  }
  ticks0=$(tree_ticks); sleep "${AGENT_SAMPLE:-$SAMPLE}"; ticks1=$(tree_ticks)
  tck=$(getconf CLK_TCK 2>/dev/null || echo 100)
  pct=$(awk -v d=$((ticks1 - ticks0)) -v h="$tck" -v s="${AGENT_SAMPLE:-$SAMPLE}" 'BEGIN {printf "%.1f", 100 * d / h / s}')
  if awk -v p="$pct" -v m="${AGENT_MAX_PCT:-2}" 'BEGIN {exit !(p < m)}'; then echo "idle $pct%"; else echo "$pct%"; fi
  awk -v p="$pct" -v m="${AGENT_MAX_PCT:-2}" 'BEGIN {exit !(p < m)}'
}
compilers=$(awk -v self=$$ '$1 != self && ($2 == "bend" || $0 ~ /bend2\/main\.ts/)' <<< "$plist")
if [ -n "$others" ] && [ "${AGENTS_IDLE_OK:-0}" = 1 ] && [ -z "$compilers" ]; then
  if a=$(agents_idle); then
    check other_processes "$others, agents $a" ok
  else
    check other_processes "$others, agents $a" busy
  fi
else
  check other_processes "${others:-none}" "$([ -z "$others" ] && echo ok || echo busy)"
fi

paranoid=$(cat "$PROC/sys/kernel/perf_event_paranoid" 2>/dev/null || echo unknown)
check perf_event_paranoid "$paranoid" "$([[ $paranoid =~ ^-?[0-9]+$ ]] && [ "$paranoid" -le 1 ] && echo ok || echo busy)"

# CPU's SMT siblings (thread_siblings_list, as "2-3" or "2,3"), each sampled from /proc/stat
siblings=$(tr ',' '\n' < "$SYS/devices/system/cpu/cpu$CPU/topology/thread_siblings_list" 2>/dev/null |
  awk -F- -v me="$CPU" '{for (c = $1; c <= ($2 == "" ? $1 : $2); c++) if (c != me) print c}')
if [ -z "$siblings" ]; then
  check "cpu${CPU}_sibling" none ok
else
  stat() { awk -v c="cpu$1" '$1 == c {print $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9, $5 + $6}' "$PROC/stat"; }
  declare -A t0 i0
  for c in $siblings; do read -r t0[$c] i0[$c] < <(stat "$c"); done
  sleep "$SAMPLE"
  for c in $siblings; do
    read -r t1 i1 < <(stat "$c")
    busy=$(awk -v dt=$((t1 - t0[$c])) -v di=$((i1 - i0[$c])) 'BEGIN {printf "%.0f", dt ? 100 * (dt - di) / dt : 0}')
    check "cpu${CPU}_sibling" "cpu$c ${busy}%" "$([ "$busy" -lt 10 ] && echo ok || echo busy)"
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
