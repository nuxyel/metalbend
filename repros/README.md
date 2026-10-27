# Repros

Minimal cases cut from the workloads, each with the same bits as its C twin. Built with `bend X.bend -o` (Bend 2.0.39)
and `clang -std=c11 -O3` (the flags `bend -o` gives clang); one thread on CPU 3, user-mode counts, busy machine.

| Case | What it shows | Bend | C | Ratio |
|---|---|---|---|---|
| `dot_mask.bend`, `dot_mask.c` | tensor-array's rotating dot over two arrays of 2^16, 4096 times: each `Array.get` keeps an `and` with the array's mask (unknown to clang), and the loop is unrolled by 2, so the rotation of 4 sums leaves register copies | 3,224 M instr, 517 M cycles | 1,008 M, 340 M | 3.2x instr, 1.52x cycles |
| `softmax_array.bend` | workloads/softmax-ce over an `Array` with tail loops instead of tensor-array's lists, the same bits | 2,362 M instr, 731 M cycles | (softmax-ce's native.c) 1,603 M, 520 M | 1.47x instr, 1.41x cycles; the lists cost 3.4x on top |

`softmax_array.bend` is not an upstream case: it shows that most of softmax-ce's distance to C is tensor-array's list
walks (a library choice), not the compiler.
