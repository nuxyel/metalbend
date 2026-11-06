#!/usr/bin/env bash
# Where the run of record that scripts/when_idle.sh waits on stands: the unit, the log's last lines, the results folder.
#   scripts/record_status.sh [unit] [log]     # defaults: metalbend-record, build/when_idle.log
cd "$(dirname "$0")/.."
unit=${1:-metalbend-record}
log=${2:-build/when_idle.log}
echo "unit $unit: $(systemctl --user is-active "$unit" 2>/dev/null)"
[ -f "$log" ] && tail -n 3 "$log" | cut -c1-200
ls -d results/*/ 2>/dev/null | tail -n 1
