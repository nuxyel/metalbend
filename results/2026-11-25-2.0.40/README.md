# 2026-11-25-2.0.40: llama-token's run of record, the corpus on Bend 2.0.40 again

`scripts/launch.sh 2.0.40` (5 rounds), started at 01:28 -04:00 by `scripts/when_idle.sh` from a user unit after five
passing preflights in a row, right after another measurement of the same idle round (the first 70 seconds): the same
steps as `../2026-11-06-2.0.40/`, now with `llama-token`, the sixteenth workload. The preflight found the machine idle
with `AGENTS_IDLE_OK=1` (load 0.02, one Claude Code session open and idle, CPU 3's sibling at 1%, mains power,
`performance` profile). Every hash its oracle in `oracles.tsv` (86 cases).

The numbers are in `report.md`, `summary.md` and `probe-1781.tsv`; `llama-token`'s line is in `NOTES.md`
(2026-11-25) and the README's "What it has found". The other fifteen workloads repeat the launch run's 2.0.40
cycles within 3% (`read-native` 2.9%, `matvec-bands` 1.5%, the rest under 1%); the README's other numbers stay the
launch run's.
