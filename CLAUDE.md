# MetalBend

A corpus of real ML workloads for Bend 2's compiler: each with a spec, a bit oracle, a handwritten C target and
hardware-counter timings, run on every Bend release. The fourth project after bend-ml, llama.bend and BendTorch
(chosen 2026-10-25; the analysis is in Renan's private notes, never linked from here). Private again since 2026-10-27 (public for about an
hour that day); the launch is Renan's call. Nothing is pushed to `main` without him.

## Where things are

- `docs/plan-v1.md`: the current plan and its next steps (`docs/plan-v0.md` before it). `docs/format.md`: the files
  1.x keeps stable; `docs/VERSIONING.md`: release numbers.
- `NOTES.md` (from the first experiment on): every finding and measurement, by date.
- `workloads/<name>/`: `main.bend`, later `native.c` (same bits), `gpu.bend` (a GPU target, `make check-gpu`),
  `README.md`. `repros/`: minimal upstream cases. `run.sh`: build and measure. `results/<date>/`: one line per run.
- The workloads come from bend-ml, llama.bend and BendTorch (their published packages, pinned in the import lines);
  their `NOTES.md` hold the experiments behind each one.

## Rules

1. Read bend-ml's `CLAUDE.md` ("pitfalls") before writing Bend. Bend's working pin is **2.0.39**; the
   corpus runs older versions and `main` on purpose.
2. Every workload prints a hash of its full output; a run whose hash differs from the oracle is a finding, never
   noise.
3. Timings: one thread pinned with `taskset -c 3` (`CPU=3`, run.sh's default), `perf stat` instructions and cycles in user mode
   (the kernel's share varies between runs), on mains power in the
   `performance` profile, the machine idle. A busy-machine number is labeled as such.
4. Measure kernels inside their largest program too, not only in a probe (shared memory `probe-vs-program`).
5. Method and analysis beyond a one-line result belong in Renan's private notes, never named or linked from here; this
   repository holds workloads, oracles, targets, the scripts and the raw results. Issue and comment texts for
   upstream are drafted outside it too; a minimal case an issue carries goes in `repros/`.
6. The name is a plain English verb. No characters, logos, images, quotes or other material from any TV series or
   franchise, in any file, post or slide.
7. Work on `devel`; small commits, one logical change each; no attribution lines or session links.
