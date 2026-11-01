#!/usr/bin/env bash
# Moves MetalBend's Bend pin to a new release (as llama.bend's scripts/bump_bend.sh does): downloads the two Linux
# tarballs, computes their SHA256 (the release publishes no checksums file) and rewrites the pin where it is a pin:
# scripts/setup.sh (version and both sums), scripts/check_oracles.sh's PIN, CLAUDE.md's rule 1, the Makefile's setup
# line, CI's setup step (its cache key hashes setup.sh, so the cache follows by itself), the README's setup line and
# run.sh's default range. run.sh also learns where the new release's fixed copy lives (~/.bend-<version>/bin/bend, as
# for 2.0.37-2.0.39) and runs it by default. Dated text (NOTES.md, results/, plans) is history and stays. It installs
# nothing and runs no check; the steps after it are printed at the end.
#
#   scripts/bump_bend.sh 2.0.40
set -euo pipefail
NEW=${1:?usage: scripts/bump_bend.sh <version>}
cd "$(dirname "$0")/.."
OLD=$(sed -n 's/^BEND_VERSION=//p' scripts/setup.sh)
[ "$OLD" != "$NEW" ] || { echo "already on $NEW"; exit 0; }
# run.sh's names: a 2.0.x release by its last number, a later one in full
name() { case $1 in 2.0.*) echo "${1##*.}" ;; *) echo "$1" ;; esac; }
OLDN=$(name "$OLD"); NEWN=$(name "$NEW")
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
sum() { # arch
  local f="bend-$NEW-linux-$1.tar.gz"
  curl --proto '=https' --tlsv1.2 -fsSL -o "$TMP/$f" "https://github.com/bendlang/bend/releases/download/v$NEW/$f"
  sha256sum "$TMP/$f" | awk '{print $1}'
}
X64=$(sum x64); ARM=$(sum arm64)
OLDX64=$(sed -n 's/.*Linux-x86_64)  OS=linux; ARCH=x64;   SHA=\([0-9a-f]*\) ;;/\1/p' scripts/setup.sh)
OLDARM=$(sed -n 's/.*Linux-aarch64) OS=linux; ARCH=arm64; SHA=\([0-9a-f]*\) ;;/\1/p' scripts/setup.sh)
[ -n "$OLDX64" ] && [ -n "$OLDARM" ] || { echo "setup.sh: SHA lines not found"; exit 1; }
# a dot in a version is literal in these patterns
o=${OLD//./\\.}
sed -i "s/$OLDX64/$X64/; s/$OLDARM/$ARM/; s/^BEND_VERSION=$o$/BEND_VERSION=$NEW/; s/Bend $o/Bend $NEW/g" scripts/setup.sh
sed -i "s/^PIN=$o$/PIN=$NEW/" scripts/check_oracles.sh
sed -i "s/Bend's working pin is \*\*$o\*\*/Bend's working pin is **$NEW**/" CLAUDE.md
sed -i "s/install the pinned Bend ($o)/install the pinned Bend ($NEW)/" Makefile
sed -i "s/Set up (Bend $o,/Set up (Bend $NEW,/" .github/workflows/ci.yml
sed -i "s/^make setup     # Bend $o (checked by SHA256)/make setup     # Bend $NEW (checked by SHA256)/; s/Bend 2\.0\.35-$o, 5 rounds/Bend 2.0.35-$NEW, 5 rounds/" README.md
# run.sh: the new release's fixed copy, after the old one's line, and in the default versions
sed -i "/^    $OLDN) echo \"\$HOME\/.bend-$o\/bin\/bend\" ;;$/a\\    $NEWN) echo \"\$HOME/.bend-$NEW/bin/bend\" ;;" run.sh
sed -i "s/^VERSIONS=\${VERSIONS:-\"\(.*\) $OLDN\"}$/VERSIONS=\${VERSIONS:-\"\1 $OLDN $NEWN\"}/" run.sh
grep -q "^    $NEWN) echo \"\$HOME/.bend-$NEW/bin/bend\" ;;$" run.sh || { echo "run.sh: the line for $OLD not found"; exit 1; }
grep -q "^VERSIONS=.* $NEWN\"}$" run.sh || { echo "run.sh: the default VERSIONS not found"; exit 1; }
grep -q "^PIN=$NEW$" scripts/check_oracles.sh || { echo "check_oracles.sh: PIN not found"; exit 1; }
echo "Bend $OLD -> $NEW"
echo "  linux-x64   $X64"
echo "  linux-arm64 $ARM"
git --no-pager diff --stat
cat <<EOF
next:
  1. a fixed copy of $NEW at ~/.bend-$NEW (the release's tarball, as setup.sh unpacks it), for run.sh's "$NEWN"
  2. make setup (installs $NEW into ~/.bend), then make check, make check-gpu, make test, make laws, make mutate
  3. a NOTES.md entry; oracles.tsv changes only with a finding, both hashes recorded
EOF
