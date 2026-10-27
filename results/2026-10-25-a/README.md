# 2026-10-25-a (superseded by 2026-10-25-b)

The first run, counting user and kernel mode together: every pair's instructions came out in two modes ~0.8% apart,
with cycles ~17% apart, from the kernel's share (page faults, transparent huge pages set to `always`). Kept as it
was; `run.sh` counts user mode since. Busy machine (load 2.7-3.8). Same findings as 2026-10-25-b.
