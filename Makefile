# MetalBend's checks: the bits of every workload and C target against oracles.tsv, the tools' unit tests, and a
# mutation run over both. No timings: run.sh and release.sh measure, on an idle machine. `make setup` first.
export BEND_NO_TELEMETRY := 1
export PATH := $(HOME)/.bend/bin:$(HOME)/.elan/bin:$(PATH)
PY := python3 -I

.PHONY: setup data check check-gpu test laws mutate launch

setup:            ## install the pinned Bend (2.0.40) and Lean (4.34.0) if missing; check clang and Python 3
	scripts/setup.sh

data:             ## data/dense.bin and data/bf16.safetensors, the read workloads' inputs (deterministic)
	$(PY) lib/gen_dense.py
	$(PY) lib/gen_bf16.py

check:            ## build every workload (1 and 16 threads) and every native.c, fail on a hash that is not its oracle
	scripts/check_oracles.sh

check-gpu:        ## local, CI has no GPU: every gpu.bend built with CUDA, on the GPU and with --gpu off (1, 16 threads); skips with no GPU
	TARGETS=gpu scripts/check_oracles.sh

test:             ## analyze.py, chart.py, oracle_diff.py, run.sh's guard and the GPU lane's skip on synthetic runs; release.sh on a fake upstream (needs bun); count.sh, track.sh, track_verdict.py, bisect.sh and the history's scripts on fakes
	$(PY) -m unittest discover -s tests -v

laws:             ## the ten laws of laws/ check (with --verdict) and each of their 22 mutants is refused
	cd laws && ./check.sh

mutate:           ## break the corpus and the tools on purpose; every mutant must be caught (scripts/mutate.py)
	$(PY) scripts/mutate.py

launch:           ## launch day on a release, VERSION=2.0.40: preflight, check-gpu, GPU=1 release.sh, probe, chart, report
	scripts/launch.sh $(VERSION)
