#!/usr/bin/env bash
# One-shot, idempotent setup for the checks (make check, make test, make mutate). No sudo.
#
#   scripts/setup.sh      # Bend 2.0.39 into ~/.bend (checked by SHA256), Lean 4.34.0, then clang and Python 3 checked
#
# The same install steps as BendTorch's scripts/setup.sh. run.sh's other versions and perf are for timing, which the
# checks do not do.
set -euo pipefail

BEND_VERSION=2.0.39
LEAN_VERSION=4.34.0

cd "$(dirname "$0")/.."
export BEND_NO_TELEMETRY=1
export PATH="$HOME/.bend/bin:$HOME/.elan/bin:$PATH"

say() { printf '\n== %s\n' "$*"; }
have_lean() { command -v lean >/dev/null 2>&1 && lean --version 2>/dev/null | grep -q "version $LEAN_VERSION"; }
have_bend() { command -v bend >/dev/null 2>&1 && [ "$(bend version 2>/dev/null | awk '{print $NF}')" = "$BEND_VERSION" ]; }

say "Bend $BEND_VERSION"
if have_bend; then
  echo "already installed"
else
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64)  OS=linux; ARCH=x64;   SHA=6cf462fd8f70b094a4950ebb709a9c4ffd8f1d1189d9cedf1fd63cd5d041c7ab ;;
    Linux-aarch64) OS=linux; ARCH=arm64; SHA=71b43e1bb9313dd14ac2b0553b854e41c39d65ecaa47040796ebff4a46f54a97 ;;
    *) echo "unsupported platform $(uname -s)-$(uname -m): Bend runs on Linux (use WSL on Windows)"; exit 1 ;;
  esac
  HOME_BEND=${BEND_HOME:-$HOME/.bend}
  TMP=$(mktemp -d)
  trap 'rm -rf "$TMP"' EXIT
  NAME="bend-$BEND_VERSION-$OS-$ARCH.tar.gz"
  curl --proto '=https' --tlsv1.2 -fsSL -o "$TMP/$NAME" "https://github.com/bendlang/bend/releases/download/v$BEND_VERSION/$NAME"
  echo "$SHA  $TMP/$NAME" | sha256sum -c - >/dev/null || { echo "SHA256 mismatch for $NAME"; exit 1; }
  tar -xzf "$TMP/$NAME" -C "$TMP" 2>/dev/null
  mkdir -p "$HOME_BEND/bin"
  rm -rf "$HOME_BEND/bend2" "$HOME_BEND/guide"
  mv "$TMP/bend/bend2" "$TMP/bend/guide" "$HOME_BEND/"
  mv -f "$TMP/bend/bin/bend" "$HOME_BEND/bin/bend"
fi
have_bend || { echo "ERROR: bend $BEND_VERSION not found after install"; exit 1; }
bend version

# the kernel behind `bend --verdict`, which make laws runs
say "Lean $LEAN_VERSION"
if have_lean; then
  echo "already installed"
else
  curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
    | sh -s -- -y --no-modify-path --default-toolchain "leanprover/lean4:v$LEAN_VERSION"
fi
have_lean || { echo "ERROR: lean $LEAN_VERSION not found after install"; exit 1; }
lean --version

say "clang and Python"
command -v clang >/dev/null || { echo "ERROR: clang not found (bend -o and the C targets need it)"; exit 1; }
clang --version | head -1
python3 --version

say "setup finished: make check (the bits), make test (the tools), make laws (the proofs), make mutate"
