#!/usr/bin/env bash
# Waits for an idle machine, then runs a command: scripts/preflight.sh every STEP seconds (60), and the command once
# the preflight has passed QUIET times in a row (5: five quiet minutes with the defaults), giving up after MAX_WAIT
# hours (24). Detached, with agent sessions left open and idle (preflight.sh's AGENTS_IDLE_OK), as a user unit so that
# it is in no agent's process tree:
#   systemd-run --user --unit=metalbend-record --working-directory=$PWD --setenv=AGENTS_IDLE_OK=1 --setenv=PATH="$PATH" \
#     -p StandardOutput=append:$PWD/build/when_idle.log -p StandardError=append:$PWD/build/when_idle.log \
#     scripts/when_idle.sh scripts/launch.sh 2.0.40
# Its environment reaches the command, so run.sh's own preflight lines see AGENTS_IDLE_OK too. Each line of the log
# names what was busy; NOTIFY=1 (the default when notify-send exists) also says on the desktop when the command starts
# and how it ended. The exit status is the command's.
set -uo pipefail
cd "$(dirname "$0")/.."
STEP=${STEP:-60}
QUIET=${QUIET:-5}
MAX_WAIT=${MAX_WAIT:-24}
NOTIFY=${NOTIFY:-$(command -v notify-send >/dev/null && echo 1 || echo 0)}
[ $# -gt 0 ] || { echo "usage: scripts/when_idle.sh <command...>"; exit 2; }
note() { [ "$NOTIFY" = 1 ] && notify-send -a MetalBend "MetalBend" "$1" 2>/dev/null || true; }
deadline=$(($(date +%s) + MAX_WAIT * 3600))
ok=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  if out=$(scripts/preflight.sh 2>&1); then ok=$((ok + 1)); else ok=0; fi
  why=$(awk '$1 == "busy" {$1 = ""; sub(/^ +/, ""); printf "%s%s", (n++ ? "; " : ""), $0}' <<< "$out")
  echo "$(date -Is) $([ -n "$why" ] && echo "busy: $why" || echo idle) ($ok/$QUIET)"
  if [ "$ok" -ge "$QUIET" ]; then
    printf '%s\n' "$out"
    echo "$(date -Is) when_idle: running $*"
    note "Machine idle: running $*"
    "$@"
    st=$?
    echo "$(date -Is) when_idle: $* exited $st"
    note "$* exited $st$([ "$st" = 0 ] && echo ': done' || echo ': read the log')"
    exit "$st"
  fi
  sleep "$STEP"
done
echo "$(date -Is) when_idle: no idle window in $MAX_WAIT h"
note "No idle window in $MAX_WAIT h: $* did not run"
exit 1
