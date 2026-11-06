"""Mutation testing: break the corpus or its tools on purpose and check that a gate catches the change.

Each mutant replaces one exact piece of text in one file, runs the gate that should see it, and restores the file.
A mutant is caught when its gate fails. The gates are the bits check (scripts/check_oracles.sh, on the one workload
and target the mutant touches, one thread) and the unit tests (tests/). Some mutants are expected to survive: they
compute the same bits (an equivalent mutant) or change what no input reaches; those carry their reason, so the report
shows the limits of the checks as well as their reach.

    python3 -I scripts/mutate.py        # or: make mutate
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(os.environ, BEND_NO_TELEMETRY="1", PATH=f"{Path.home()}/.bend/bin:{os.environ['PATH']}")
OUT = ROOT / "build" / "mutate"


def oracle(workload, target):
    """The bits check on one workload: its Bend build on one thread ("bend") or its C target ("c")."""
    def gate():
        env = dict(ENV, WORKLOADS=workload, TARGETS=target, THREADS="1", OUT=str(OUT))
        return subprocess.run(["scripts/check_oracles.sh"], cwd=ROOT, env=env, capture_output=True).returncode == 0
    gate.__name__ = f"oracle {workload} {target}"
    return gate


def fresh_data(workload, target, data="dense.bin"):
    """The bits check on a workload that reads data/<data>, with the file written again by its lib/gen_*.py."""
    inner = oracle(workload, target)
    dense = ROOT / "data" / data

    def gate():
        kept = dense.with_suffix(".kept")
        had = dense.exists()
        if had:
            dense.rename(kept)
        try:
            return inner()
        finally:
            if had:
                dense.unlink(missing_ok=True)
                kept.rename(dense)
    gate.__name__ = f"fresh data, {inner.__name__}"
    return gate


def tests(module):
    def gate():
        return subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-p", f"{module}.py"],
                              cwd=ROOT, env=ENV, capture_output=True).returncode == 0
    gate.__name__ = f"tests {module}"
    return gate


ANALYZE, CHART, GUARD = tests("test_analyze"), tests("test_chart"), tests("test_run_guard")

# (name, file, before, after, gate, expected): expected is "caught", or the reason the mutant may survive
MUTANTS = [
    # the workloads' programs
    ("softmax-ce: the first round's seed", "workloads/softmax-ce/main.bend",
     "go(6n, 7, TA.Mat.zeros(64n, 49152n))", "go(6n, 8, TA.Mat.zeros(64n, 49152n))", oracle("softmax-ce", "bend"), "caught"),
    ("softmax-ce: the labels' shift", "workloads/softmax-ce/main.bend",
     "((i * 2654435761 : U32) >> 7n)", "((i * 2654435761 : U32) >> 8n)", oracle("softmax-ce", "bend"), "caught"),
    ("matvec-bands: one token fewer", "workloads/matvec-bands/main.bend",
     "go(24n, W{", "go(23n, W{", oracle("matvec-bands", "bend"), "caught"),
    ("matvec-bands: a band's second child takes the first one's seed", "workloads/matvec-bands/main.bend",
     "((seed * 2 : U32) + 2 : U32), s)", "((seed * 2 : U32) + 1 : U32), s)", oracle("matvec-bands", "bend"), "caught"),
    ("gemm-tile8: the forward product's B from another seed", "lib/gemm.bend",
     "TT.rmat(1536n, 576n, 2)", "TT.rmat(1536n, 576n, 7)", oracle("gemm-tile8", "bend"), "caught"),
    ("gemm-fork: one repetition fewer", "workloads/gemm-fork/main.bend",
     "G.run(8n, 3n)", "G.run(7n, 3n)", oracle("gemm-fork", "bend"), "caught"),
    ("gemm-fork: two levels of parallel blocks instead of three", "workloads/gemm-fork/main.bend",
     "G.run(8n, 3n)", "G.run(8n, 2n)", oracle("gemm-fork", "bend"),
     "equivalent: tensor-fork's blocks give the same bits at any depth (the reason gemm-fork and gemm-tile8 share an oracle)"),
    ("mnist-step: one batch fewer", "workloads/mnist-step/main.bend",
     "tloop(200n, 0, 0.1,", "tloop(199n, 0, 0.1,", oracle("mnist-step", "bend"), "caught"),
    ("adamw: the second moment's decay", "workloads/adamw/main.bend",
     "(p2 * 0.999 : F32), T.Opt.mat", "(p2 * 0.99 : F32), T.Opt.mat", oracle("adamw", "bend"), "caught"),
    ("block-step: twice the weight decay", "workloads/block-step/main.bend",
     "T.CAdamW{0.001, 0.9, 0.999, 0.00000001, 0.01, 0.1, 0.001}", "T.CAdamW{0.001, 0.9, 0.999, 0.00000001, 0.02, 0.1, 0.001}",
     oracle("block-step", "bend"), "caught"),
    ("attention-step: one step fewer", "workloads/attention-step/main.bend",
     "tloop(4n, 0, cfg()", "tloop(3n, 0, cfg()", oracle("attention-step", "bend"), "caught"),
    ("rmsnorm-step: one step fewer", "workloads/rmsnorm-step/main.bend",
     "tloop(200n, 0, cfg()", "tloop(199n, 0, cfg()", oracle("rmsnorm-step", "bend"), "caught"),
    ("rmsnorm-step: the state's hash leaves out the second moment", "workloads/rmsnorm-step/main.bend",
     "U32.to_nat((3 * NP() : U32))", "U32.to_nat((2 * NP() : U32))", oracle("rmsnorm-step", "bend"), "caught"),
    ("read-native: one block fewer", "workloads/read-native/main.bend",
     "blocks(16n, 0, f,", "blocks(15n, 0, f,", oracle("read-native", "bend"), "caught"),
    ("read-binary: the read starts one cell late", "workloads/read-binary/main.bend",
     "R.read_f32(f, 0, 4194304,", "R.read_f32(f, 4, 4194304,", oracle("read-binary", "bend"), "caught"),
    ("softmax-ce-array: the first round's seed", "workloads/softmax-ce-array/main.bend",
     "go(6n, 7, TA.Mat.zeros(64n, 49152n))", "go(6n, 8, TA.Mat.zeros(64n, 49152n))", oracle("softmax-ce-array", "bend"),
     "caught"),
    ("mnist-fork: one batch fewer", "workloads/mnist-fork/main.bend",
     "tloop(200n, 0, 0.1,", "tloop(199n, 0, 0.1,", oracle("mnist-fork", "bend"), "caught"),
    ("mnist-fork: the first layer's product in one block", "workloads/mnist-fork/main.bend",
     "TF.matmul(100n, 784n, 128n, 3n, x, w1)", "TF.matmul(100n, 784n, 128n, 0n, x, w1)", oracle("mnist-fork", "bend"),
     "equivalent: tensor-fork's blocks give the same bits at any depth (the reason mnist-fork prints mnist-step's hashes)"),
    ("read-bf16: the two layers read in the other order", "workloads/read-bf16/main.bend",
     'layer("model.layers.0.", layer("model.layers.1.", Nil{}))',
     'layer("model.layers.1.", layer("model.layers.0.", Nil{}))', oracle("read-bf16", "bend"), "caught"),
    ("read-bf16: k_proj and v_proj swapped", "workloads/read-bf16/main.bend",
     'p ++ "self_attn.k_proj.weight"', 'p ++ "self_attn.v_proj.weight"', oracle("read-bf16", "bend"), "caught"),
    ("bpe-encode: one merge fewer", "workloads/bpe-encode/main.bend",
     "BPE.train(256n, 0n,", "BPE.train(255n, 0n,", oracle("bpe-encode", "bend"), "caught"),
    # the C targets
    ("softmax-ce-array C: exp in single precision, through softmax-ce's C", "workloads/softmax-ce/native.c",
     "e[j] = (float)exp((double)(row[j] - m));", "e[j] = expf(row[j] - m);", oracle("softmax-ce-array", "c"), "caught"),
    ("mnist-fork C: the ReLU's gradient passes zeros, through mnist-step's C", "workloads/mnist-step/native.c",
     "(z1[t] > 0.0f ? 1.0f : 0.0f)", "(z1[t] >= 0.0f ? 1.0f : 0.0f)", oracle("mnist-fork", "c"), "caught"),
    ("read-bf16 C: a BF16 widened one bit short", "workloads/read-bf16/native.c",
     "u2f((uint32_t)buf[i] << 16)", "u2f((uint32_t)buf[i] << 15)", oracle("read-bf16", "c"), "caught"),
    ("read-bf16 C: the data counted from the header's start", "workloads/read-bf16/native.c",
     "fseek(f, (long)(8 + len + b), SEEK_SET)", "fseek(f, (long)(8 + b), SEEK_SET)", oracle("read-bf16", "c"), "caught"),
    ("bpe-encode C: a tie goes to the pair that appears last", "workloads/bpe-encode/native.c",
     "if (cnt[order[k]] > cnt[best]) best", "if (cnt[order[k]] >= cnt[best]) best", oracle("bpe-encode", "c"), "caught"),
    ("bpe-encode C: merges overlap", "workloads/bpe-encode/native.c",
     "{ t[o++] = c; i += 2; }", "{ t[o++] = c; i += 1; }", oracle("bpe-encode", "c"), "caught"),
    ("matvec-bands C: the four sums joined in another order", "workloads/matvec-bands/native.c",
     "y[j] = (a0 + a1) + (a2 + a3);", "y[j] = (a0 + a2) + (a1 + a3);", oracle("matvec-bands", "c"), "caught"),
    ("matvec-bands C: the operands of one addition swapped", "workloads/matvec-bands/native.c",
     "y[j] = (a0 + a1) + (a2 + a3);", "y[j] = (a1 + a0) + (a2 + a3);", oracle("matvec-bands", "c"),
     "equivalent: IEEE 754 addition is commutative, bit for bit"),
    ("softmax-ce C: the row's max takes ties from the right", "workloads/softmax-ce/native.c",
     "for (int j = 1; j < C; j++) m = m < row[j] ? row[j] : m;", "for (int j = 1; j < C; j++) m = m <= row[j] ? row[j] : m;",
     oracle("softmax-ce", "c"), "equivalent here: a tie picks an equal number, and the logits hold no -0 or NaN, the only "
     "values where the two differ"),
    ("softmax-ce C: exp in single precision", "workloads/softmax-ce/native.c",
     "e[j] = (float)exp((double)(row[j] - m));", "e[j] = expf(row[j] - m);", oracle("softmax-ce", "c"), "caught"),
    ("mnist-step C: the ReLU's gradient passes zeros", "workloads/mnist-step/native.c",
     "(z1[t] > 0.0f ? 1.0f : 0.0f)", "(z1[t] >= 0.0f ? 1.0f : 0.0f)", oracle("mnist-step", "c"), "caught"),
    ("adamw C: a larger epsilon", "workloads/adamw/native.c",
     "eps = 0.00000001f", "eps = 0.0000001f", oracle("adamw", "c"), "caught"),
    ("gemm-tile8 C: a product's third partial sum takes the fourth cell", "workloads/gemm-tile8/native.c",
     "s2 = s2 + x[p + 2] * y[p + 2];", "s2 = s2 + x[p + 3] * y[p + 3];", oracle("gemm-tile8", "c"), "caught"),
    ("gemm-fork C: a column block leaves out its last column", "workloads/gemm-fork/native.c",
     "for (int j = j0; j < j0 + cnt; j++)", "for (int j = j0; j < j0 + cnt - 1; j++)", oracle("gemm-fork", "c"), "caught"),
    ("read-native C: the hash skips the last cell", "workloads/read-native/native.c",
     "mb_show_hash(a, N);", "mb_show_hash(a, N - 1);", oracle("read-native", "c"), "caught"),
    ("lib/bt.h: RMSNorm without its epsilon", "lib/bt.h",
     "return 1.0f / (float)sqrt((double)(s / (float)d + eps));", "return 1.0f / (float)sqrt((double)(s / (float)d));",
     oracle("rmsnorm-step", "c"), "caught"),
    ("lib/bt.h: the causal mask lets a row see one key fewer", "lib/bt.h",
     "for (int l = 0; l <= i; l++) { row[l] = (float)exp", "for (int l = 0; l < i; l++) { row[l] = (float)exp",
     oracle("attention-step", "c"), "caught"),
    ("lib/bt.h: SiLU as x times the reciprocal, not x over the sum", "lib/bt.h",
     "static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)); }",
     "static inline float bt_silu(float x) { return x * (1.0f / (1.0f + (float)exp((double)-x))); }",
     oracle("block-step", "c"), "caught"),
    ("lib/bt.h: SiLU's exp in single precision", "lib/bt.h",
     "static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)); }",
     "static inline float bt_silu(float x) { return x / (1.0f + expf(-x)); }", oracle("block-step", "c"), "caught"),
    ("lib/bt.h: SiLU plus 1e-7", "lib/bt.h",
     "static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)); }",
     "static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)) + 1e-7f; }",
     oracle("block-step", "c"), "caught"),
    ("lib/bt.h: SiLU gives zeros", "lib/bt.h",
     "static inline float bt_silu(float x) { return x / (1.0f + (float)exp((double)-x)); }",
     "static inline float bt_silu(float x) { return 0.0f * x; }", oracle("block-step", "c"), "caught"),
    ("lib/bt.h: the state's hash leaves out the second moments", "lib/bt.h",
     "  for (int i = 0; i < k; i++) h = mb_fnv(h, ps[i]->v, ps[i]->n);\n", "", oracle("attention-step", "c"), "caught"),
    # the shared pieces
    ("mb.bend: the hash's FNV prime", "lib/mb.bend",
     "* 16777619 : U32)", "* 16777617 : U32)", oracle("matvec-bands", "bend"), "caught"),
    ("mb.bend: the hash starts at cell 1", "lib/mb.bend",
     "hash_go(n, 1, 2166136261, Array.get(F32, a, 0))", "hash_go(n, 2, 2166136261, Array.get(F32, a, 1))",
     oracle("read-native", "bend"), "caught"),
    ("mb.bend: the inputs' multiplier", "lib/mb.bend",
     "* 2654435761 : U32) .^. (i >> 13n", "* 2654435769 : U32) .^. (i >> 13n", oracle("softmax-ce", "bend"), "caught"),
    ("mb.h: the hash's FNV prime", "lib/mb.h",
     "* 16777619u;", "* 16777617u;", oracle("matvec-bands", "c"), "caught"),
    ("mb.h: the inputs' second multiplier", "lib/mb.h",
     "(h * 2246822519u)", "(h * 2246822517u)", oracle("adamw", "c"), "caught"),
    ("mb.h: calloc's arguments swapped", "lib/mb.h",
     "calloc(n, sizeof(float))", "calloc(sizeof(float), n)", oracle("matvec-bands", "c"),
     "equivalent: the same number of zeroed bytes"),
    ("gen_dense.py: another seed", "lib/gen_dense.py",
     "SEED = 9", "SEED = 8", fresh_data("read-native", "c"), "caught"),
    ("gen_bf16.py: another seed", "lib/gen_bf16.py",
     "SEED = 11", "SEED = 12", fresh_data("read-bf16", "c", "bf16.safetensors"), "caught"),
    ("oracles.tsv: one digit of an oracle", "oracles.tsv",
     "softmax-ce\tdebeda8b7bc50c1f", "softmax-ce\tdebeda8b7bc50c1e", oracle("softmax-ce", "c"), "caught"),
    # the tools
    ("analyze.py: beyond noise at 2x the spread", "analyze.py",
     "abs(d) > 3 * noise", "abs(d) > 2 * noise", ANALYZE, "caught"),
    ("analyze.py: beyond noise at 4x the spread", "analyze.py",
     "abs(d) > 3 * noise", "abs(d) > 4 * noise", ANALYZE, "caught"),
    ("analyze.py: beyond noise from exactly 3x", "analyze.py",
     "abs(d) > 3 * noise", "abs(d) >= 3 * noise", ANALYZE,
     "differs only when a change is exactly 3x the noise in binary floating point, which no run reaches"),
    ("analyze.py: the noise is the smaller spread", "analyze.py",
     "max(si, spread(bc[\"ins\"]), 0.001)", "max(min(si, spread(bc[\"ins\"])), 0.001)", ANALYZE, "caught"),
    ("analyze.py: an instruction floor of 0.01%", "analyze.py",
     "spread(bc[\"ins\"]), 0.001)", "spread(bc[\"ins\"]), 0.0001)", ANALYZE, "caught"),
    ("analyze.py: a cycle floor of 0.1%", "analyze.py",
     "spread(bc[\"cyc\"]), 0.01)", "spread(bc[\"cyc\"]), 0.001)", ANALYZE, "caught"),
    ("analyze.py: two rounds are enough", "analyze.py",
     "min(len(c[\"ins\"]), len(bc[\"ins\"])) >= 3", "min(len(c[\"ins\"]), len(bc[\"ins\"])) >= 2", ANALYZE, "caught"),
    ("analyze.py: the spread is over the mean", "analyze.py",
     "    m = statistics.median(xs)\n    return", "    m = statistics.mean(xs)\n    return", ANALYZE, "caught"),
    ("analyze.py: an output that differs across versions is not listed", "analyze.py",
     "elif bhash and hs != bhash:", "elif False:", ANALYZE, "caught"),
    ("analyze.py: a C target's output is not compared", "analyze.py",
     "same = c[\"hash\"] == bc[\"hash\"] and len(c[\"hash\"]) == 1", "same = True", ANALYZE, "caught"),
    ("analyze.py: thread counts may print two outputs", "analyze.py",
     "same = len(hashes[(w, v)]) == 1", "same = len(hashes[(w, v)]) <= 2", ANALYZE, "caught"),
    ("analyze.py: 16-thread runs join the one-thread medians", "analyze.py",
     "runs = [r for r in allruns if r[\"threads\"] == 1]", "runs = allruns", ANALYZE, "caught"),
    ("chart.py: the C ratio upside down", "scripts/chart.py",
     "statistics.median(cyc[VERSION]) / statistics.median(cyc[\"c\"])",
     "statistics.median(cyc[\"c\"]) / statistics.median(cyc[VERSION])", CHART, "caught"),
    ("chart.py: the C ratio reads every thread count", "scripts/chart.py",
     "ok(r) and int(r.get(\"threads\") or 1) == 1 and", "ok(r) and", CHART, "caught"),
    ("chart.py: the speedup reads failed runs", "scripts/chart.py",
     "if r[\"bend\"] == VERSION and r[\"status\"] == \"ok\":", "if r[\"bend\"] == VERSION:", CHART, "caught"),
    ("run.sh: the guard takes any count for one thread", "run.sh",
     "ok=$([ \"$peak\" = 1 ] && echo y || echo n)", "ok=y", GUARD, "caught"),
    ("run.sh: the guard takes fewer threads than asked", "run.sh",
     "[ \"$peak\" -ge \"$t\" ] && [ \"$peak\" -le", "[ \"$peak\" -ge 1 ] && [ \"$peak\" -le", GUARD, "caught"),
    ("run.sh: the guard takes many more threads than asked", "run.sh",
     "[ \"$peak\" -le $((t + 2)) ]", "[ \"$peak\" -le $((t + 20)) ]", GUARD, "caught"),
]


def main():
    os.chdir(ROOT)
    escaped = []
    # every gate must pass on the code as it is, or each of its mutants would count as caught without being tested
    for gate in dict.fromkeys(m[4] for m in MUTANTS):
        if not gate():
            print(f"mutate: the gate '{gate.__name__}' fails on the unmutated code")
            sys.exit(1)
    for name, path, before, after, gate, expected in MUTANTS:
        p = ROOT / path
        src = p.read_text()
        assert src.count(before) == 1, f"{name}: the text to mutate is not in {path} exactly once"
        try:
            p.write_text(src.replace(before, after, 1))
            caught = not gate()
        finally:
            p.write_text(src)
        verdict = "caught" if caught else "survived"
        ok = caught == (expected == "caught")
        print(f"{'ok ' if ok else 'BAD'} {verdict:8} {name}" + ("" if expected == "caught" else f"  [{expected}]"),
              flush=True)
        if not ok:
            escaped.append(name)
    shutil.rmtree(OUT, ignore_errors=True)
    survived = sum(1 for m in MUTANTS if m[5] != "caught")
    print(f"mutate: {len(MUTANTS)} mutants, {len(MUTANTS) - len(escaped)} as expected "
          f"({len(MUTANTS) - survived} caught, {survived} expected to survive)")
    if escaped:
        print("mutate: not as expected: " + "; ".join(escaped))
    sys.exit(1 if escaped else 0)


if __name__ == "__main__":
    main()
