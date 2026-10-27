"""Writes data/dense.bin: 4,194,304 little-endian F32, lib/mb.bend's val(9, i), for the dense-read workloads.

    python3 -I lib/gen_dense.py

x - 1.5 for x in [1, 2) is exact in F32, so computing it in double gives the same bits as mb.bend.
"""
import array
import os
import sys

M = 0xFFFFFFFF
N = 4194304
SEED = 9


def main():
    assert sys.byteorder == "little"
    words = array.array("I")
    for i in range(N):
        h = (((i + SEED) * 2654435761) & M) ^ (i >> 13)
        g = ((h * 2246822519) & M) ^ (h >> 16)
        words.append((g >> 9) | 1065353216)
    out = array.array("f", (x - 1.5 for x in array.array("f", words.tobytes())))
    os.makedirs("data", exist_ok=True)
    with open("data/dense.bin", "wb") as f:
        out.tofile(f)


if __name__ == "__main__":
    main()
