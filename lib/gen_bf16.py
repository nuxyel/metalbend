"""Writes data/bf16.safetensors, read-bf16's input: two SmolLM2-135M decoder layers' weights as BF16 in the
safetensors format, 7,080,192 numbers (14 MB), deterministic.

    python3 -I lib/gen_bf16.py

The file is laid out as Hugging Face writes one: 8 bytes holding the header's length (little-endian), a JSON header
padded with spaces to a multiple of 8, then each tensor's bytes in the header's order (names sorted). Tensor t of that
order holds lib/mb.bend's val(11 + t, i) for its cells i, cut to BF16 (the top 16 bits of the F32); read-bf16 widens
each one back exactly (the low 16 bits zero).
"""
import array
import json
import os
import struct
import sys

M = 0xFFFFFFFF
SEED = 11
HIDDEN, KV, FF = 576, 192, 1536


def layer(i):
    p = f"model.layers.{i}."
    return [
        (p + "input_layernorm.weight", [HIDDEN]),
        (p + "self_attn.q_proj.weight", [HIDDEN, HIDDEN]),
        (p + "self_attn.k_proj.weight", [KV, HIDDEN]),
        (p + "self_attn.v_proj.weight", [KV, HIDDEN]),
        (p + "self_attn.o_proj.weight", [HIDDEN, HIDDEN]),
        (p + "post_attention_layernorm.weight", [HIDDEN]),
        (p + "mlp.gate_proj.weight", [FF, HIDDEN]),
        (p + "mlp.up_proj.weight", [FF, HIDDEN]),
        (p + "mlp.down_proj.weight", [HIDDEN, FF]),
    ]


# the tensors in the model's order (the order read-bf16 asks for them); the file holds them sorted by name
TENSORS = layer(0) + layer(1)


def cells(shape):
    n = 1
    for d in shape:
        n *= d
    return n


def bf16(seed, n):
    """val(seed, i) for i < n, as BF16: x - 1.5 for x in [1, 2) is exact in F32, so double gives mb.bend's bits."""
    words = array.array("I")
    for i in range(n):
        h = (((i + seed) * 2654435761) & M) ^ (i >> 13)
        g = ((h * 2246822519) & M) ^ (h >> 16)
        words.append((g >> 9) | 1065353216)
    f32 = array.array("f", (x - 1.5 for x in array.array("f", words.tobytes())))
    return array.array("H", (w >> 16 for w in array.array("I", f32.tobytes())))


def main():
    assert sys.byteorder == "little"
    names = sorted(TENSORS)
    header, off = {"__metadata__": {"format": "pt"}}, 0
    for name, shape in names:
        size = 2 * cells(shape)
        header[name] = {"dtype": "BF16", "shape": shape, "data_offsets": [off, off + size]}
        off += size
    text = json.dumps(header, separators=(",", ":")).encode()
    text += b" " * (-len(text) % 8)
    os.makedirs("data", exist_ok=True)
    with open("data/bf16.safetensors", "wb") as f:
        f.write(struct.pack("<Q", len(text)))
        f.write(text)
        for t, (name, shape) in enumerate(names):
            bf16(SEED + t, cells(shape)).tofile(f)


if __name__ == "__main__":
    main()
