#!/usr/bin/env bash
# The gate for laws/: PROOF.bend must check (with --verdict too), and each mutant of the Tile8 model must make it fail.
#   laws/check.sh
# A mutant is t8_dotr.bend with one line of t8 changed (sed), checked in a scratch copy of this folder.
set -euo pipefail
cd "$(dirname "$0")"
BEND=${BEND:-$HOME/.bend/bin/bend}
"$BEND" PROOF.bend | grep -q "ALL PROOFS CHECK" || { echo "PROOF.bend fails"; exit 1; }
"$BEND" PROOF.bend --verdict | grep -q "ALL PROOFS CHECK" || { echo "PROOF.bend fails --verdict"; exit 1; }
echo "law t8_is_dotr: checks, and --verdict"
mutants=(
  # lane 0 adds product 4 before product 0: the same sum over the reals, other bits in F32
  's/Add{Add{s0, Mul{x0, y0}}, Mul{x4, y4}}/Add{Add{s0, Mul{x4, y4}}, Mul{x0, y0}}/'
  # lanes 1 and 2 swap their second products
  's/Add{Add{s1, Mul{x1, y1}}, Mul{x5, y5}}, Add{Add{s2, Mul{x2, y2}}, Mul{x6, y6}}/Add{Add{s1, Mul{x1, y1}}, Mul{x6, y6}}, Add{Add{s2, Mul{x2, y2}}, Mul{x5, y5}}/'
  # the four sums combined in another pairing at the end
  's/case _ _: fin(s0, s1, s2, s3)/case _ _: fin(s0, s2, s1, s3)/'
  # the first pair added as s1 + s0: harmless in F32, whose addition commutes, so no numeric test can see it; the law
  # rejects it too, because it assumes nothing about Add: it is stricter than "the same bits"
  's/case _ _: fin(s0, s1, s2, s3)/case _ _: fin(s1, s0, s2, s3)/'
)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
for m in "${mutants[@]}"; do
  cp LAWS.bend PROOF.bend "$tmp/"
  sed "$m" t8_dotr.bend > "$tmp/t8_dotr.bend"
  if cmp -s t8_dotr.bend "$tmp/t8_dotr.bend"; then echo "mutant did not apply: $m"; fail=1; continue; fi
  if "$BEND" "$tmp/PROOF.bend" 2>&1 | grep -q "ALL PROOFS CHECK"; then echo "mutant survived: $m"; fail=1
  else echo "mutant rejected: $m"; fi
done
exit $fail
