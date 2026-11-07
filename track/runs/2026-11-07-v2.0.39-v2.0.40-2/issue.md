Bend v2.0.40 (624dd9f4607c) against v2.0.39 (a3efe8a3801f), every workload counted under Cachegrind on one thread with both versions on one machine (clang 18.1.3, valgrind 3.22.0). A finding is a change in instructions beyond 0.1% or in simulated D1 misses beyond 5%, or an output that is not its oracle.

| workload | instructions | D1 misses | output | verdict |
|---|---:|---:|---|---|
| bpe-encode | +9.42% | 2.03x | its oracle | regression |

- bpe-encode: instructions +9.42%, D1 misses 2.03x

To count them again, from a clone of this repository (bun, clang and valgrind on PATH):

```sh
make data
scripts/count.sh v2.0.39 bpe-encode
scripts/count.sh v2.0.40 bpe-encode
```

The counts: `track/runs/2026-11-07-v2.0.39-v2.0.40-2/` on the `data` branch.
The run: https://github.com/nuxyel/metalbend/actions/runs/42384646460.
