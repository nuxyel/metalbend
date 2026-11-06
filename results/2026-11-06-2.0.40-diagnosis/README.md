# 2026-11-06-2.0.40-diagnosis: the launch run on Bend 2.0.40, on a machine with agent sessions open (not the run of record)

`scripts/launch.sh 2.0.40` (5 rounds, at d470585), started by a night script at 00:54 -04:00 after a 30-minute wait for
a clean preflight: preflight, `make check-gpu`, `GPU=1 ./release.sh 2.0.40` (2.0.39 and 2.0.40 built from their tags with
bun, 1 and 16 threads, the C targets and the three GPU targets under nsys), the #1781 probe (2.0.40 has
`Array.get_unchecked`), `report.md`. Its preflight's only busy check was `other_processes`: two idle Claude Code
sessions (one waiting on the night script), so it ran with `BUSY_OK=1` and `summary.md` marks it busy. Load 1.10 at the
start. The folder was written as `results/2026-11-06-2.0.40` and renamed, with `docs/results-2.0.40.svg` moved in as
`results-2.0.40.svg`, so the run of record (agents closed) keeps that name and `docs/` is left as it was. 375 CPU runs
and the GPU runs, every hash its oracle in `oracles.tsv` (81 cases).

The numbers are in `report.md` and `summary.md`; what they say is in `NOTES.md` (2026-11-06).
