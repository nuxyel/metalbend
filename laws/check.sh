#!/usr/bin/env bash
# The gate for laws/: PROOF.bend must check (with --verdict too), proving every law of LAWS.bend, and every mutant of
# mutants.sh must make it fail.
#   laws/check.sh
set -euo pipefail
cd "$(dirname "$0")"
BEND=${BEND:-$HOME/.bend/bin/bend}
"$BEND" PROOF.bend | grep -q "ALL PROOFS CHECK" || { echo "PROOF.bend fails"; exit 1; }
"$BEND" PROOF.bend --verdict | grep -q "ALL PROOFS CHECK" || { echo "PROOF.bend fails --verdict"; exit 1; }
for law in $(sed -n 's/^law \([a-z0-9_]*\):$/\1/p' LAWS.bend); do echo "law $law: checks, and --verdict"; done
BEND=$BEND ./mutants.sh
