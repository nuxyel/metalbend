# Versioning

I number MetalBend releases `MAJOR.MINOR.PATCH`, tagged `vX.Y.Z` on `main` through a release pull request `devel` ->
`main`, the way bend-ml numbers its own. MetalBend publishes no package, so the number is about the corpus and its
tools: what a result written by one release means to another.

| Part | When it changes | Example |
|---|---|---|
| MAJOR | results written by the old release can no longer be read or compared by the new one: a column of `runs.tsv` or `env.tsv` changes meaning or goes away, `run.sh`'s or `release.sh`'s interface breaks, or the oracle stops being a hash of the whole output | 1.0: the first stable format (`docs/format.md`) |
| MINOR | something new that old results still sit next to: a workload, a C target, a lane (the GPU's), a law, a new column or option | 1.1: a workload cut from a new package |
| PATCH | fixes to the tools, documentation, the results of a new Bend release run, a pin bumped without changing what a workload computes | 1.0.1: 2.0.41's results |

Rules that keep old results comparable:

- A workload's name means one computation. When what it computes or prints changes (a new input size, the final weights
  added to its hash), its old and new hashes both go in `NOTES.md` with the date, and its results before that date are
  read with the old hash. The change is MINOR.
- The packages a workload imports stay at exact versions. Moving a pin that changes the work (a faster kernel in a new
  package version) is a new workload or a MINOR change recorded the same way; moving one that does not is a PATCH.
- `results/` is append-only: a folder is never rewritten after its `README.md` is written. A rerun goes in a new folder.

Before 1.0.0 (2026-10-25..27) the corpus had no tags; `NOTES.md` and `docs/plan-v0.md`, `docs/plan-v1.md` are its
history.
