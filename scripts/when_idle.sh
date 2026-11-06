#!/usr/bin/env bash
# Waits for an idle machine, then runs a command: scripts/preflight.sh every STEP seconds (60), and the command once
# the preflight has passed QUIET times in a row (5: five quiet minutes with the defaults), giving up after MAX_WAIT
# hours (24). Detached, with agent sessions left open and idle (preflight.sh's AGENTS_IDLE_OK):
#   AGENTS_IDLE_OK=1 setsid -f scripts/when_idle.sh scripts/launch.sh 2.0.40 > when_idle.log 2>&1 < /dev/null
# Its environment reaches the command, so run.sh's own preflight lines see AGENTS_IDLE_OK too. Detached, it is in no
# agent's process tree, so its preflights and the run do not count as an agent's work.
set -uo pipefail
cd "$(dirname "$0")/.."
STEP=${STEP:-60}
QUIET=${QUIET:-5}
MAX_WAIT=${MAX_WAIT:-24}
[ $# -gt 0 ] || { echo "usage: scripts/when_idle.sh <command...>"; exit 2; }
deadline=$(($(date +%s) + MAX_WAIT * 3600))
ok=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if out=$(scripts/preflight.sh 2>&1); then ok=$((ok + 1)); else ok=0; fi
  echo "$(date -Is) $(tail -1 <<< "$out") ($ok/$QUIET)"
  if [ "$ok" -ge "$QUIET" ]; then
    printf '%s\n' "$out"
    echo "$(date -Is) when_idle: running $*"
    exec "$@"
  fi
  sleep "$STEP"
done
echo "$(date -Is) when_idle: no idle window in $MAX_WAIT h"
exit 1
