#!/usr/bin/env bash
# Mutants of laws/: each one changes one line of a scratch copy of this folder (a model, a statement, or tensor-array's
# own code), and PROOF.bend must fail on every one. check.sh runs it after the proofs; it also runs alone.
#   laws/mutants.sh             (VERBOSE=1 also shows where the checker stopped on each)
# A mutant of tensor-array changes a copy of the published 0.1.16.0 (as bend caches it) and points the copy of laws/ at
# it; that copy must still check by itself, so the failure comes from these laws, not from tensor-array's own.
set -euo pipefail
cd "$(dirname "$0")"
BEND=${BEND:-$HOME/.bend/bin/bend}
TA_IMPORT='bend-ml-tensor-array@0.1.16.0/main.bend'
TA_SRC=${TA_SRC:-$HOME/.bend/lib/0x0159e1f0f11cc1d285ac6a993d19ba8a/main.bend}
[ -f "$TA_SRC" ] || "$BEND" PROOF.bend --check-only > /dev/null || true
grep -q "tensor-array@0.1.16.0" "$TA_SRC" 2>/dev/null || { echo "tensor-array 0.1.16.0 not found at $TA_SRC (set TA_SRC)"; exit 1; }

# target file, sed expression, what it breaks
mutants=(
  # t8_is_dotr
  t8_dotr.bend 's/Add{Add{s0, Mul{x0, y0}}, Mul{x4, y4}}/Add{Add{s0, Mul{x4, y4}}, Mul{x0, y0}}/'
    "Tile8: lane 0 adds product 4 before product 0 (the same sum over the reals, other bits in F32)"
  t8_dotr.bend 's/Add{Add{s1, Mul{x1, y1}}, Mul{x5, y5}}, Add{Add{s2, Mul{x2, y2}}, Mul{x6, y6}}/Add{Add{s1, Mul{x1, y1}}, Mul{x6, y6}}, Add{Add{s2, Mul{x2, y2}}, Mul{x5, y5}}/'
    "Tile8: lanes 1 and 2 swap their second products"
  t8_dotr.bend 's/case _ _: fin(s0, s1, s2, s3)/case _ _: fin(s0, s2, s1, s3)/'
    "Tile8: the four sums combined in another pairing"
  t8_dotr.bend 's/case _ _: fin(s0, s1, s2, s3)/case _ _: fin(s1, s0, s2, s3)/'
    "Tile8: the first pair added as s1 + s0 (harmless in F32, whose addition commutes: the law is stricter)"
  # bands_len, matvec_l_len: tensor-array's own code
  ta 's/bv_mat(r, c, rr, x, m)/bv_mat(r, c, half(rr), x, m)/'
    "tensor-array: a band multiplies only the first half of its rows"
  ta 's/bv_gemm(r, c, rr, rr, x, w)/bv_gemm(r, c, Nat.sub(rr, 1n), rr, x, w)/'
    "tensor-array: a band reads back one number fewer than its rows"
  LAWS.bend 's/{TA.bl_len(r, c, TA.bmv(c, r, b, rr, e, xp)) == rr : Nat}/{TA.bl_len(r, c, TA.bmv(c, r, b, rr, e, xp)) == 1n+rr : Nat}/'
    "statement: bands_len claims one number more than the rows"
)

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
n=0
for ((k = 0; k < ${#mutants[@]}; k += 3)); do
  target=${mutants[k]} expr=${mutants[k+1]} why=${mutants[k+2]}
  rm -rf "$tmp/m"; mkdir "$tmp/m"
  cp ./*.bend "$tmp/m/"
  if [ "$target" = ta ]; then
    sed "$expr" "$TA_SRC" > "$tmp/m/ta.bend"
    if cmp -s "$TA_SRC" "$tmp/m/ta.bend"; then echo "mutant did not apply: $why"; fail=1; continue; fi
    if ! "$BEND" "$tmp/m/ta.bend" --check-only 2>&1 | grep -q "ALL PROOFS CHECK"; then
      echo "mutant breaks tensor-array itself: $why"; fail=1; continue
    fi
    sed -i "s|$TA_IMPORT|./ta.bend|" "$tmp/m/"*.bend
  else
    sed "$expr" "$target" > "$tmp/m/$target"
    if cmp -s "$target" "$tmp/m/$target"; then echo "mutant did not apply: $why"; fail=1; continue; fi
  fi
  n=$((n + 1))
  out=$("$BEND" "$tmp/m/PROOF.bend" 2>&1 || true)
  if grep -q "ALL PROOFS CHECK" <<< "$out"; then echo "mutant survived: $why"; fail=1
  else
    echo "mutant rejected: $why"
    # VERBOSE=1 shows where the checker stopped
    [ -n "${VERBOSE:-}" ] && grep -m1 -A1 "^Location" <<< "$out" | sed 's/^/    /'
  fi
done
[ $fail = 0 ] && echo "all $n mutants rejected"
exit $fail
