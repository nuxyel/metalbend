# MetalBend's checks: the bits of every workload and C target against oracles.tsv, the tools' unit tests, and a
# mutation run over both. No timings: run.sh and release.sh measure, on an idle machine. `make setup` first.
export BEND_NO_TELEMETRY := 1
export PATH := $(HOME)/.bend/bin:$(HOME)/.elan/bin:$(PATH)
PY := python3 -I

.PHONY: setup data check test laws mutate

setup:            ## install the pinned Bend (2.0.39) and Lean (4.34.0) if missing; check clang and Python 3
	scripts/setup.sh

data:             ## data/dense.bin, the dense-read workloads' input (deterministic)
	$(PY) lib/gen_dense.py

check:            ## build every workload (1 and 16 threads) and every native.c, fail on a hash that is not its oracle
	scripts/check_oracles.sh

test:             ## analyze.py, scripts/chart.py and run.sh's thread guard on synthetic runs
	$(PY) -m unittest discover -s tests -v

laws:             ## the ten laws of laws/ check (with --verdict) and each of their 22 mutants is refused
	cd laws && ./check.sh

mutate:           ## break the corpus and the tools on purpose; every mutant must be caught (scripts/mutate.py)
	$(PY) scripts/mutate.py
