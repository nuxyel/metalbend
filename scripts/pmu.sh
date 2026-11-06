# Sourced by run.sh and the probes: which CPU a one-thread run is pinned to, and which perf PMU counts it.
#   . scripts/pmu.sh; taskset -c "$CPU" perf stat -e "$(pmu_events one)" ...
# CPU (3 by default, a P-core of the Core Ultra 7 155H the results come from) is the CPU a one-thread run is pinned to.
# A hybrid Intel CPU has two PMUs, cpu_core (P-cores) and cpu_atom (E-cores); any other machine has one, `cpu`.
# PMU_ONE is the PMU of CPU's own core type (cpu_core for a P-core, cpu_atom for an E-core, `cpu` with one PMU), and
# PMU_ALL every PMU there is, for a run on more threads that may land on both core types. PMU_DEVICES
# (/sys/bus/event_source/devices) is for the tests.
CPU=${CPU:-3}
PMU_DEVICES=${PMU_DEVICES:-/sys/bus/event_source/devices}
# whether CPU $1 is in a PMU's cpus list ("0-11" or "12-19,22")
pmu_has_cpu() {
  tr ',' '\n' < "$PMU_DEVICES/$2/cpus" 2>/dev/null |
    awk -F- -v c="$1" '{if (c >= $1 && c <= ($2 == "" ? $1 : $2)) f = 1} END {exit !f}'
}
if [ -d "$PMU_DEVICES/cpu_core" ]; then
  PMU_ALL="cpu_core"
  [ -d "$PMU_DEVICES/cpu_atom" ] && PMU_ALL="cpu_core cpu_atom"
  if [ -d "$PMU_DEVICES/cpu_atom" ] && pmu_has_cpu "$CPU" cpu_atom; then PMU_ONE=cpu_atom; else PMU_ONE=cpu_core; fi
else
  PMU_ALL=cpu PMU_ONE=cpu
fi
# perf stat's event list: `one` for a run pinned to CPU (user- and kernel-mode instructions and cycles of its PMU),
# `many` for a run on more threads (user-mode instructions of every PMU, summed by the reader; cycles of the
# first PMU only, so not comparable); the probes build their own lists from PMU_ONE
pmu_events() {
  local p ev
  if [ "$1" = one ]; then
    echo "$PMU_ONE/instructions/u,$PMU_ONE/cycles/u,$PMU_ONE/instructions/k,$PMU_ONE/cycles/k"
  else
    ev=""
    for p in $PMU_ALL; do ev="$ev${ev:+,}$p/instructions/u"; done
    p=${PMU_ALL%% *}
    echo "$ev,$p/cycles/u,$p/instructions/k,$p/cycles/k"
  fi
}
