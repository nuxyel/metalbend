# 2026-11-01-2.0.39-rehearsal: launch day rehearsed on Bend 2.0.39, 5 rounds (not the run of record)

`BUSY_OK=1 ROUNDS=5 OUT=results/2026-11-01-2.0.39-rehearsal scripts/launch.sh 2.0.39`, at fa39309 with the fifteen
workloads of 1.0: preflight, `make check-gpu` (9 runs, every hash its oracle), `GPU=1 ./release.sh 2.0.39` (2.0.38 and
2.0.39 built from their tags with bun, 1 and 16 threads, the C targets and the three GPU targets under nsys), the #1781
probe skipped (v2.0.39 lacks a888ef27), `report.md`. A dress rehearsal approved by Renan: the run of record is the
2.0.40 launch run, and these numbers are not cited in the README or the posts in its place.

Machine: mains, `performance` profile, CPU 3's sibling (CPU 4) 0% busy, `perf_event_paranoid` 1, load 0.30 at the
first preflight and 1.96 at the start of release.sh (just after `check-gpu`), 1.02-2.68 before the runs (round means
1.50, 1.09, 1.82, 1.59, 1.59), 1.05 at the end. `env.tsv` says `busy other_processes`, and `summary.md` marks the run
busy for it: the processes were three idle Codex processes (0.0% CPU over a 3 s sample) and the Claude Code session
driving this run (under 3.5%), nothing else; every other check was clean. 405 runs (375 CPU, 30 GPU), every hash its
oracle in `oracles.tsv`.

`results-2.0.39.svg` is `scripts/chart.py 39` on this folder (it needed the labels of the four new workloads,
fixed the same day); `docs/results-2.0.39.svg` is left as it was. The GPU build products `make check-gpu` left here
(launch.sh passed its `OUT` on to it, fixed the same day) were removed before this folder was committed.
