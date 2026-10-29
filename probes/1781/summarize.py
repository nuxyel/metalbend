# Min-max of each binary's user-mode instructions, cycles and wall seconds in count.sh's output, its spread in
# instructions and the hashes it printed (the seconds count only from an idle machine).
#   python3 -I probes/1781/summarize.py probes/1781/results/<file>.tsv
import collections
import csv
import sys

d = collections.OrderedDict()
for r in csv.DictReader(open(sys.argv[1]), delimiter="\t"):
    d.setdefault(r["binary"], []).append(r)
for b, rs in d.items():
    ins = [int(r["instructions_u"]) for r in rs]
    cyc = [int(r["cycles_u"]) for r in rs]
    sec = [float(r["seconds"]) for r in rs]
    hs = ",".join(sorted({r["hash"] for r in rs}))
    print(f"{b:26} n={len(rs)} instr {min(ins) / 1e6:10.2f} M (spread {max(ins) - min(ins):>5})"
          f"  cycles {min(cyc) / 1e6:6.0f}-{max(cyc) / 1e6:6.0f} M  {min(sec):.3f}-{max(sec):.3f} s  {hs}")
