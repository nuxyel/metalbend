# 2026-11-06-2.0.40: the launch run on Bend 2.0.40, the run of record

`scripts/launch.sh 2.0.40` (5 rounds, at b286a6b), started at 11:19 -04:00 by `scripts/when_idle.sh` from a user unit
after five passing preflights in a row: preflight, `make check-gpu` (with the pinned 2.0.39), `GPU=1 ./release.sh 2.0.40`
(2.0.39 and 2.0.40 built from their tags with bun, 1 and 16 threads, the C targets and the three GPU targets under nsys),
the #1781 probe (2.0.40 has `Array.get_unchecked`), `report.md`, and `docs/results-2.0.40.svg`. The preflight found the
machine idle with `AGENTS_IDLE_OK=1`: load 0.50, two Claude Code sessions open and idle (1.3% of one CPU over the
sample), CPU 3's sibling at 0%, mains power, `performance` profile; `summary.md` does not mark it busy. Every hash its
oracle in `oracles.tsv` (81 cases).

The numbers are in `report.md`, `summary.md` and `probe-1781.tsv`; what they say is in `NOTES.md` (2026-11-06) and the
README's "What it has found".
