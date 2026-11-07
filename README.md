# MetalBend's release watch: the data

This branch holds what the release watch (`.github/workflows/track.yml`) writes: for each comparison of two Bend
versions, every workload of the corpus counted under Cachegrind on one GitHub runner, both versions in the same job.
The workflow writes it; nothing here is edited by hand.

- `track/last-tag`: the last release of bendlang/bend that the daily run compared. The next run looks for the release
  after it. It starts at v2.0.40, the release MetalBend's run of record measured (`results/2026-11-06-2.0.40/`).
- `track/index.tsv`: one row per comparison: its folder, the two refs and their commits, the trigger (`daily`, or
  `by-hand` for a run with refs given), how many workloads moved, how many of them went to an issue, the run.
- `track/runs/<date>-<old>-<new>/`: `counts.tsv` (`scripts/count.sh`'s rows for both Bends), `env.tsv` (the runner,
  clang, valgrind, bun, MetalBend's commit), `verdict.tsv` and `report.md` (`scripts/track_verdict.py`), and
  `issue.md` with `issue-title.txt` when the comparison had a regression or a changed output.

The format is in `docs/format.md` ("The release watch"). Cachegrind's instructions are a simulator's count of a binary
built by the runner's clang: compare the two Bends within one folder, never across folders, and never with the perf
counts of `results/`.
