# Writes the tensor-array 0.1.16.0 variants and the two workloads that import them, under build/p1781/src/<variant>/.
# dotr reads the next number of both lines at every step, so its last step reads one number past each line: at the end
# of a band (2^20 numbers) or of x (2^11) that index is the array's capacity, which Array.get wraps to 0 and
# Array.get_unchecked must not be given. Two shapes that stop before it, with the same sums in the same order:
#   last: checked reads, dotr gets a third case (1n) that adds the last product and stops
#   km1:  checked reads, dotg runs dotr for k - 1 steps and dotr's 0n case adds the last product (the loop keeps its
#         two cases)
#   u:    km1 with Array.get_unchecked in dotr's loop and in t8_dot's loop (both @unsafe)
#   u0:   the published shape with the unchecked reads: one read past each line, outside the contract; only to show
#         the mask alone on the same loop
# t8_dot keeps its shape: its read past the last cell of a line stays inside the packed array's capacity for every
# shape of gemm-tile8 (n * ceil(k / 8) is never a power of two there), so its unchecked read keeps the contract.
#   python3 -I probes/1781/gen.py <path of tensor-array 0.1.16.0's main.bend>
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(sys.argv[1]).read()
PKG = "import bend-ml-tensor-array@0.1.16.0/main.bend as TA"

DOTR_OLD = """    case 0n Tuple{a, x} Tuple{b, y}:
      R{a, b, ((a0 + a1 : F32) + (a2 + a3 : F32) : F32)}
    case 1n+p Tuple{a, +x} Tuple{b, +y}:
      dotr(p, """
DOTR_LAST = """    case 0n Tuple{a, x} Tuple{b, y}:
      R{a, b, ((a0 + a1 : F32) + (a2 + a3 : F32) : F32)}
    case 1n Tuple{a, +x} Tuple{b, +y}:
      R{a, b, ((a1 + a2 : F32) + (a3 + (a0 + (x * y : F32) : F32) : F32) : F32)}
    case 2n+p Tuple{a, +x} Tuple{b, +y}:
      dotr(1n+p, """
DOTR_KM1 = """    case 0n Tuple{a, +x} Tuple{b, +y}:
      R{a, b, ((a1 + a2 : F32) + (a3 + (a0 + (x * y : F32) : F32) : F32) : F32)}
    case 1n+p Tuple{a, +x} Tuple{b, +y}:
      dotr(p, """
DOTG_OLD = """def dotg(k: Nat, +ia: U32, +ib: U32, +sa: U32, +sb: U32, acc: F32, ra: Array<F32> & F32, rb: Array<F32> & F32) -> R:
  dotr(k, ia, ib, sa, sb, acc, 0.0, 0.0, 0.0, ra, rb)
"""
DOTG_KM1 = """def dot0(+acc: F32, ra: Array<F32> & F32, rb: Array<F32> & F32) -> R:
  match ra rb:
    case Tuple{a, x} Tuple{b, y}:
      R{a, b, ((acc + 0.0 : F32) + (0.0 + 0.0 : F32) : F32)}

def dotg(k: Nat, +ia: U32, +ib: U32, +sa: U32, +sb: U32, acc: F32, ra: Array<F32> & F32, rb: Array<F32> & F32) -> R:
  match k:
    case 0n:
      dot0(acc, ra, rb)
    case 1n+p:
      dotr(p, ia, ib, sa, sb, acc, 0.0, 0.0, 0.0, ra, rb)
"""
DOTR_READS = "Array.get(F32, a, (ia + sa : U32)), Array.get(F32, b, (ib + sb : U32)))"
T8_READS = "Array.get(T8, a, (ia + 1 : U32)), Array.get(T8, b, (ib + 1 : U32)))"


def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def unchecked(text):
    text = once(text, DOTR_READS, DOTR_READS.replace("Array.get(", "Array.get_unchecked("))
    text = once(text, T8_READS, T8_READS.replace("Array.get(", "Array.get_unchecked("))
    text = once(text, "def dotr(", "@unsafe\ndef dotr(")
    return once(text, "def t8_dot(", "@unsafe\ndef t8_dot(")


last = once(src, DOTR_OLD, DOTR_LAST)
km1 = once(once(src, DOTR_OLD, DOTR_KM1), DOTG_OLD, DOTG_KM1)
u = unchecked(km1)
u0 = unchecked(src)


for name, lib in [("last", last), ("km1", km1), ("u", u), ("u0", u0)]:
    out = os.path.join(root, "build", "p1781", "src", name)
    os.makedirs(os.path.join(out, "lib"), exist_ok=True)
    open(os.path.join(out, "lib", "ta_lib.bend"), "w").write(lib)
    for f in ["mb.bend", "ta.bend", "gemm.bend"]:
        text = open(os.path.join(root, "lib", f)).read()
        if PKG in text:
            text = once(text, PKG, "import ./ta_lib.bend as TA")
        open(os.path.join(out, "lib", f), "w").write(text)
    for w in ["matvec-bands", "gemm-tile8"]:
        os.makedirs(os.path.join(out, "workloads", w), exist_ok=True)
        text = open(os.path.join(root, "workloads", w, "main.bend")).read()
        if PKG in text:
            text = once(text, PKG, "import ../../lib/ta_lib.bend as TA")
        open(os.path.join(out, "workloads", w, "main.bend"), "w").write(text)
    print(out)
