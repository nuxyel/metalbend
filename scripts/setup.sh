#!/usr/bin/env bash
# One-shot, idempotent setup for the checks (make check, make test, make mutate). No sudo.
#
#   scripts/setup.sh      # Bend 2.0.40 into ~/.bend (checked by SHA256), Lean 4.34.0, then clang and Python 3 checked
#
# The same install steps as BendTorch's scripts/setup.sh. run.sh's other versions and perf are for timing, which the
# checks do not do.
set -euo pipefail

BEND_VERSION=2.0.40
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
    Linux-x86_64)  OS=linux; ARCH=x64;   SHA=c9ff8d67bd903fb6ad9a26b43d8a62c01021de82a44d55ce4a3dcd4732113d6b ;;
    Linux-aarch64) OS=linux; ARCH=arm64; SHA=2f42a6fa34ecdaa71ae105e5fa734f9a07e129d333e45448ab6d2ff03a837570 ;;
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
