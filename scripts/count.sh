#!/usr/bin/env bash
# One workload counted under Cachegrind with one Bend: its instructions (Ir) and the simulated D1 and last-level cache
# misses, exact on any machine under any load, and its output's hash against oracles.tsv. The release watch
# (scripts/track.sh, .github/workflows/track.yml) is built on it; perf's counts on an idle machine stay with run.sh.
#   scripts/count.sh v2.0.40 bpe-encode               # a ref of bendlang/bend: a tag, a branch of origin or a commit
#   scripts/count.sh ~/.bend-2.0.39/bin/bend adamw    # a Bend binary, or a wrapper from scripts/bend_main.sh
#   scripts/count.sh path/to/bend adamw               # a bendlang/bend source tree (its bend2/main.ts, bun installed)
#   HEADER=1 scripts/count.sh v2.0.40 adamw           # the column names first
#   scripts/count.sh --header                         # only them
#   REF=v2.0.40 scripts/count.sh build/bin/at-v2.0.40 adamw   # a Bend already built, its row named by the ref
# It prints one TSV row: ref (REF, or the first argument), commit, version, workload, ir, d1_misses, ll_misses, hash,
# bits, clang, valgrind. bits is ok, DIFF (the hash is not the workload's oracle), compile-failed or run-failed (then
# the counts are "-"), and the exit status 0, 1, 3 or 4 with it; 2 when the Bend cannot be built or named, and the
# commit is the source tree's (a wrapper's or a ref's) or a binary's sha256. A ref is built by scripts/bend_main.sh
# into build/bin/at-<ref> (its tree under build/src, kept by commit); the workload into build/count/<commit>/<w>, built
# again only when missing, older than its main.bend or a file of lib/, or with REBUILD=1; Cachegrind's file for
# cg_annotate goes next to it (<w>.cachegrind), the output, Cachegrind's report and the build's log too.
# One thread, and the caches given explicitly (a Core Ultra 7 155H's P-core: L1i 64 KiB 16-way, L1d 48 KiB 12-way,
# LL 24 MiB 12-way, 64-byte lines), so every machine simulates the same ones. The counts are the machine's and its
# clang's, though: compare two Bends counted on one machine, never across machines.
set -uo pipefail
cd "$(dirname "$0")/.."
export BEND_NO_TELEMETRY=1
COLS="ref\tcommit\tversion\tworkload\tir\td1_misses\tll_misses\thash\tbits\tclang\tvalgrind"
[ "${1:-}" = --header ] && { echo -e "$COLS"; exit 0; }
arg=${1:?usage: scripts/count.sh <bend ref, binary or source tree> <workload>}
w=${2:?usage: scripts/count.sh <bend ref, binary or source tree> <workload>}
[ "${HEADER:-0}" = 1 ] && echo -e "$COLS"
[ -f "workloads/$w/main.bend" ] || { echo "no workload $w" >&2; exit 2; }
vgbin=$(command -v valgrind) || { echo "count.sh needs valgrind" >&2; exit 2; }
mkdir -p build/bin
safe() { echo "$1" | tr -c 'A-Za-z0-9._\n-' _; }
# the Bend: a source tree gets a wrapper like bend_main.sh's; a binary is taken as it is; anything else is a ref
if [ -d "$arg" ] && [ -f "$arg/bend2/main.ts" ]; then
  tree=$(cd "$arg" && pwd)
  commit=$(git -C "$tree" rev-parse HEAD 2>/dev/null) || commit=unknown
  bend=$PWD/build/bin/tree-$(safe "${commit:0:12}")
  printf '#!/bin/sh\nexec bun %s/bend2/main.ts "$@"\n' "$tree" > "$bend"
  chmod +x "$bend"
elif [ -f "$arg" ] && [ -x "$arg" ]; then
  bend=$(realpath "$arg")
  wt=$(sed -n 's|^exec bun \(.*\)/bend2/main\.ts .*|\1|p' "$bend" 2>/dev/null | head -1)
  if [ -n "$wt" ]; then commit=$(git -C "$wt" rev-parse HEAD 2>/dev/null) || commit=unknown
  else commit=sha256:$(sha256sum < "$bend" | cut -c1-16); fi
else
  bend=$PWD/build/bin/at-$(safe "$arg")
  BIN=$bend scripts/bend_main.sh "$arg" >&2 || { echo "count.sh: could not build Bend at $arg" >&2; exit 2; }
  commit=$(cat "$bend.commit")
fi
version=$("$bend" version 2>/dev/null | awk '{print $NF}')
[ -n "$version" ] || { echo "count.sh: $bend reports no version" >&2; exit 2; }
clang=$(clang --version 2>/dev/null | sed -n '1s/.*version \([0-9][0-9.]*\).*/\1/p')
vg=$("$vgbin" --version | sed 's/^valgrind-//')
want=$(awk -F'\t' -v w="$w" '$1 == w {print $2}' oracles.tsv)
out=$PWD/build/count/$(safe "$(echo "${commit#sha256:}" | cut -c1-12)")
mkdir -p "$out"
row() { echo -e "${REF:-$arg}\t$commit\t$version\t$w\t$1\t$2\t$3\t$4\t$5\t${clang:-?}\t$vg"; }

# the inputs of the read workloads, deterministic (make data)
[ -f data/dense.bin ] || python3 -I lib/gen_dense.py > /dev/null
[ ! -d workloads/read-bf16 ] || [ -f data/bf16.safetensors ] || python3 -I lib/gen_bf16.py > /dev/null
bin=$out/$w
stale=${REBUILD:-0}
[ -x "$bin" ] || stale=1
for f in "workloads/$w/main.bend" lib/*; do [ "$f" -nt "$bin" ] && stale=1; done
if [ "$stale" != 0 ]; then
  rm -f "$bin"
  (cd "workloads/$w" && "$bend" main.bend -o "$bin") > "$out/$w.log" 2>&1
  [ -x "$bin" ] || { row - - - - compile-failed; exit 3; }
fi
# the runtime's thread option: between +RTS and -RTS from 2.0.38 on (bendlang/bend#1530), bare before
if [ "$(printf '%s\n' 2.0.38 "${version%%-*}" | sort -V | head -1)" = 2.0.38 ]; then rts=(+RTS --threads 1 -RTS)
else rts=(--threads 1); fi
# a fixed environment: its size moves the stack, and with it a few hundred instructions (HEADER=1 alone did)
env -i PATH=/usr/bin:/bin BEND_NO_TELEMETRY=1 \
  "$vgbin" --tool=cachegrind --cache-sim=yes --I1=65536,16,64 --D1=49152,12,64 --LL=25165824,12,64 \
  --cachegrind-out-file="$out/$w.cachegrind" "$bin" "${rts[@]}" > "$out/$w.out" 2> "$out/$w.cg" ||
  { row - - - - run-failed; exit 4; }
h=$(sha256sum < "$out/$w.out" | cut -c1-16)
# Ir, D1 misses (reads and writes) and last-level misses (instructions and data) from the file's summary line
read -r ir d1 ll < <(python3 -I - "$out/$w.cachegrind" <<'EOF'
import sys
events = summary = None
for line in open(sys.argv[1]):
    if line.startswith("events:"):
        events = line.split()[1:]
    elif line.startswith("summary:"):
        summary = [int(x) for x in line.split()[1:]]
c = dict(zip(events, summary))
print(c["Ir"], c["D1mr"] + c["D1mw"], c["ILmr"] + c["DLmr"] + c["DLmw"])
EOF
)
[ -n "${ir:-}" ] || { row - - - "$h" run-failed; exit 4; }
if [ "$h" = "$want" ]; then row "$ir" "$d1" "$ll" "$h" ok; exit 0; fi
row "$ir" "$d1" "$ll" "$h" DIFF
exit 1
