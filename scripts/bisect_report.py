"""scripts/bisect.sh's arithmetic and its report: which side of a change one Bend commit is on, and, once `git bisect`
has found the first commit with the new count, what changed at that commit.

    python3 -I scripts/bisect_report.py metrics <counts.tsv> <good commit> <bad commit>
    python3 -I scripts/bisect_report.py judge <counts.tsv> <metric> <good commit> <bad commit> <commit>
    python3 -I scripts/bisect_report.py report <dir> --workload <w> --metric <m> --good <ref> --bad <ref>
        --counts <counts.tsv> --first <commit> --parent <commit> [--subject <s>] [--pr <pr.tsv>] [--cg-dir <dir>]
        [--candidates "<commit> ..."] [--commits <n>] [--run <url>]
    python3 -I scripts/bisect_report.py plan <verdict.tsv>
    python3 -I scripts/bisect_report.py issue <report.tsv> ...

The counts are scripts/count.sh's rows, looked up by commit. A metric is `ir` (Cachegrind's instructions), `d1` (its
simulated D1 misses) or `bits` (the output against its oracle). `metrics` prints those that moved between the two
ends, with the release watch's thresholds (scripts/track_verdict.py): instructions beyond 0.1%, D1 misses beyond 5%;
`bits` alone when the bad end's output is not its oracle; exit 3 when nothing moved. `judge` prints good, bad or skip
and why: a commit is bad when its count is nearer the bad end's than the good end's (more than half the way), so one
commit that moves a little does not decide a bisect over a big change; a commit whose Bend did not build, or whose
workload did not build, run or give its oracle, is skipped (for `bits`, a changed output is bad). `report` writes
report.md, report.tsv, functions.tsv (Cachegrind's counts per function at the parent and at the first bad commit,
from <cg-dir>/<commit12>/<w>.cachegrind) and c.diff (the C each Bend emits for the workload, <dir>/<commit12>.c).
`plan` turns a release watch verdict into the bisects to run, as JSON for a workflow matrix. `issue` prints the part
of an issue that names the commits found.
"""
import csv
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from track_verdict import D1_LIMIT, IR_LIMIT, change, shown  # noqa: E402

METRICS = ("ir", "d1", "bits")
NAMES = {"ir": "instructions", "d1": "D1 misses", "bits": "output"}
COLUMN = {"ir": "ir", "d1": "d1_misses"}
MOVED_SHARE = 0.05   # a function "moved" when it carries at least 5% of the change between parent and commit
SHOWN_FUNCTIONS = 12
DIFF_LINES = 160     # the report shows this many lines of the C diff; c.diff has all of it


def read_counts(path):
    """count.sh's rows by commit (the last row of a commit wins)."""
    with open(path) as f:
        return {r["commit"]: r for r in csv.DictReader(f, delimiter="\t")}


def value(row, metric):
    return int(row[COLUMN[metric]])


def moved(good, bad):
    """The metrics that moved from the good end's row to the bad end's."""
    if good["bits"] != "ok":
        return []
    if bad["bits"] != "ok":
        return ["bits"] if bad["bits"] == "DIFF" else []
    out = []
    if abs(change(value(good, "ir"), value(bad, "ir"))) > IR_LIMIT:
        out.append("ir")
    if abs(change(value(good, "d1"), value(bad, "d1"))) > D1_LIMIT:
        out.append("d1")
    return out


def judge(rows, metric, good, bad, commit):
    """good, bad or skip for one commit, and why."""
    x = rows.get(commit)
    if x is None:
        return "skip", "no count"
    if metric == "bits":
        if x["bits"] == "ok":
            return "good", "its oracle"
        if x["bits"] == "DIFF":
            return "bad", f"hash {x['hash']}, not its oracle"
        return "skip", x["bits"]
    if x["bits"] != "ok":
        return "skip", x["bits"] if x["bits"] != "DIFF" else f"hash {x['hash']}, not its oracle"
    g, b, v = value(rows[good], metric), value(rows[bad], metric), value(x, metric)
    side = "bad" if 2 * abs(v - g) > abs(b - g) else "good"
    return side, f"{NAMES[metric]} {shown(change(g, v))} from the good end ({shown(change(g, b))} at the bad end)"


def cg_functions(path):
    """Cachegrind's counts per function name (summed over its files): {name: {"ir": n, "d1": n}}."""
    events, fn, ids, tot = None, None, {}, {}
    with open(path) as f:
        for line in f:
            if line.startswith("events:"):
                events = line.split()[1:]
            elif line.startswith("fn="):
                name = line[3:].rstrip("\n")
                m = re.match(r"\((\d+)\)(?: (.*))?$", name)
                if m:   # name compression: "(n) name" the first time, "(n)" after
                    name = ids.setdefault(m.group(1), m.group(2) or m.group(1))
                fn = name
            elif line[:1].isdigit() and fn is not None and events:
                vals = [int(x) for x in line.split()[1:]]
                acc = tot.setdefault(fn, [0] * len(events))
                for i, v in enumerate(vals[:len(events)]):
                    acc[i] += v
    if events is None:
        raise ValueError(f"{path}: no events line")
    ix = {e: i for i, e in enumerate(events)}
    return {n: {"ir": c[ix["Ir"]], "d1": c[ix["D1mr"]] + c[ix["D1mw"]]} for n, c in tot.items()}


def compare_functions(old, new, metric):
    """Per function: old and new counts, the change and its share of the whole change; largest moves first."""
    m = "ir" if metric == "bits" else metric
    rows = []
    for name in set(old) | set(new):
        a, b = old.get(name, {}).get(m, 0), new.get(name, {}).get(m, 0)
        if a != b:
            rows.append({"function": name, "old": a, "new": b, "delta": b - a})
    total = sum(r["delta"] for r in rows)
    for r in rows:
        r["share"] = r["delta"] / total if total else 0.0
        r["moved"] = abs(r["delta"]) >= MOVED_SHARE * abs(total) if total else False
    rows.sort(key=lambda r: (-abs(r["delta"]), r["function"]))
    return rows, total


# a top-level C definition: a line at column 0 with a name and its parameters, ending in "{"; the program's own
# functions are blocks opened by WL_CASE(FID_<name>), whose symbol is WL_FID_<name>
DEF = re.compile(r"^(?:[A-Za-z_]\w*[ \t*]+)+\**([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{\s*$")
CASE = re.compile(r"^\s*WL_CASE\((FID_\w+)\)")


def c_spans(lines):
    """The emitted C's definitions as (name, first line, end) spans, end exclusive."""
    spans, i = [], 0
    while i < len(lines):
        m = CASE.match(lines[i])
        if m:
            j = i + 1
            while j < len(lines) and not CASE.match(lines[j]) and not lines[j].startswith("#"):
                j += 1
            spans.append(("WL_" + m.group(1), i, j))
            i = j
            continue
        m = DEF.match(lines[i])
        if m and not lines[i].startswith("#"):
            j = i + 1
            while j < len(lines) and lines[j].rstrip() != "}":
                j += 1
            spans.append((m.group(1), i, min(j + 1, len(lines))))
            i = j + 1
            continue
        i += 1
    return spans


def c_texts(lines):
    """Each defined name's text (every definition of it, in order), and the lines outside any definition."""
    texts, inside = {}, set()
    for name, a, b in c_spans(lines):
        texts.setdefault(name, []).extend(lines[a:b])
        inside.update(range(a, b))
    texts["(outside any function)"] = [line for i, line in enumerate(lines) if i not in inside]
    return texts


def c_changes(old_lines, new_lines):
    """The definitions whose text differs: [(name, lines added, lines removed, unified diff lines)]."""
    old, new = c_texts(old_lines), c_texts(new_lines)
    out = []
    for name in sorted(set(old) | set(new)):
        a, b = old.get(name, []), new.get(name, [])
        if a == b:
            continue
        diff = list(difflib.unified_diff(a, b, f"parent/{name}", f"commit/{name}", lineterm="", n=2))
        plus = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
        minus = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
        out.append((name, plus, minus, diff))
    return out


def read_lines(path):
    p = Path(path)
    return p.read_text(errors="replace").splitlines() if p.is_file() else None


def read_tsv_kv(path):
    with open(path) as f:
        return {r["key"]: r["value"] for r in csv.DictReader(f, delimiter="\t")}


def read_pr(path):
    """number, title and url from a pr.tsv (gh api's answer as one TSV line), or Nones."""
    if path and Path(path).is_file():
        parts = Path(path).read_text().strip().split("\t")
        if len(parts) == 3 and parts[0].isdigit():
            return parts[0], parts[1], parts[2]
    return None, None, None


def commit_link(sha):
    return f"[`{sha[:12]}`](https://github.com/bendlang/bend/commit/{sha})"


def write_report(out, workload, metric, good, bad, counts, first, parent, subject="", pr=None, cg_dir="build/count",
                 candidates=(), commits=None, run=None, steps=None):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = read_counts(counts)
    gr = next((r for r in rows.values() if r["ref"] == good), None)
    br = next((r for r in rows.values() if r["ref"] == bad), None)
    if gr is None or br is None:
        raise ValueError(f"{counts}: no count for the ends {good} and {bad}")
    pr_num, pr_title, pr_url = read_pr(pr)
    fr, pr_row = rows.get(first), rows.get(parent)

    def counted(r):
        if r is None:
            return "-", "-", "-"
        if r["bits"] in ("compile-failed", "run-failed"):
            return "-", "-", r["bits"]
        return f"{int(r['ir']):,}", f"{int(r['d1_misses']):,}", "its oracle" if r["bits"] == "ok" else r["bits"]

    if metric == "bits":
        step = range_ = "the output changed"
    else:
        range_ = shown(change(value(gr, metric), value(br, metric)))
        step = shown(change(value(pr_row, metric), value(fr, metric))) if fr and pr_row and \
            fr["bits"] == pr_row["bits"] == "ok" else "-"
    clang = sorted({r["clang"] for r in rows.values()})
    vg = sorted({r["valgrind"] for r in rows.values()})

    # per function, from the two Cachegrind files
    funcs, total, cg_note = [], 0, ""
    cg_old = Path(cg_dir) / parent[:12] / f"{workload}.cachegrind"
    cg_new = Path(cg_dir) / first[:12] / f"{workload}.cachegrind"
    if cg_old.is_file() and cg_new.is_file():
        funcs, total = compare_functions(cg_functions(cg_old), cg_functions(cg_new), metric)
    else:
        cg_note = f"No Cachegrind file for {'the parent' if not cg_old.is_file() else 'the commit'}."
    with open(out / "functions.tsv", "w") as f:
        f.write("function\tparent\tcommit\tdelta\tshare\tmoved\n")
        for r in funcs:
            f.write(f"{r['function']}\t{r['old']}\t{r['new']}\t{r['delta']}\t{r['share']:.6f}\t"
                    f"{'yes' if r['moved'] else 'no'}\n")
    moved_names = [r["function"] for r in funcs if r["moved"]]

    # the emitted C, by definition
    c_old, c_new = read_lines(out / f"{parent[:12]}.c"), read_lines(out / f"{first[:12]}.c")
    changes = c_changes(c_old, c_new) if c_old is not None and c_new is not None else None
    whole = list(difflib.unified_diff(c_old or [], c_new or [], f"{parent[:12]}.c", f"{first[:12]}.c",
                                      lineterm="")) if changes is not None else []
    (out / "c.diff").write_text("\n".join(whole) + ("\n" if whole else ""))
    c_names = [c[0] for c in changes] if changes else []

    m = NAMES[metric]
    md = [f"# {workload}: {m}, {good} to {bad}", ""]
    md.append(f"`git bisect` over bendlang/bend from {good} ({commit_link(gr['commit'])}) to {bad} "
              f"({commit_link(br['commit'])}){f', {commits} commits' if commits else ''}, each step a source build of "
              f"Bend and one Cachegrind count of the workload (`scripts/bisect.sh`; clang {', '.join(clang)}, valgrind "
              f"{', '.join(vg)}). A commit is bad when its {m} are nearer the bad end's than the good end's"
              f"{'; for the output, when it is not its oracle' if metric == 'bits' else ''}; one that does not build "
              f"or whose output is not its oracle is skipped.")
    md.append("")
    if candidates:
        md.append("The bisect could not decide between skipped commits; the first bad commit is one of: " +
                  ", ".join(commit_link(c) for c in candidates) + f". Below, the earliest bad one it counted.")
        md.append("")
    md.append(f"**First bad commit:** {commit_link(first)} {subject}".rstrip())
    if pr_num:
        md.append(f"**Pull request:** [bendlang/bend#{pr_num}]({pr_url}) {pr_title}")
    md.append(f"**Change:** {m} {step} at that commit (from its parent {commit_link(parent)}), {range_} over the "
              f"whole range.")
    md += ["", "| | commit | instructions | D1 misses | output |", "|---|---|---:|---:|---|"]
    for label, r in (("good end", gr), ("parent", pr_row), ("first bad", fr), ("bad end", br)):
        ir, d1, bits = counted(r)
        sha = r["commit"][:12] if r else "-"
        md.append(f"| {label} | `{sha}` | {ir} | {d1} | {bits} |")

    if steps and Path(steps).is_file():
        with open(steps) as f:
            st = list(csv.DictReader(f, delimiter="\t"))
        md += ["", "## Steps", "", "| # | commit | instructions | D1 misses | verdict | why |", "|---:|---|---:|---:|---|---|"]
        for i, s in enumerate(st, 1):
            ir = f"{int(s['ir']):,}" if s["ir"].isdigit() else "-"
            d1 = f"{int(s['d1_misses']):,}" if s["d1_misses"].isdigit() else "-"
            md.append(f"| {i} | `{s['commit'][:12]}` {s['subject'][:70]} | {ir} | {d1} | {s['verdict']} | {s['why']} |")

    md += ["", f"## Per function, parent to first bad commit (Cachegrind, {NAMES['ir'] if metric == 'bits' else m})",
           ""]
    if funcs:
        md += [f"The functions that changed, largest first; together {total:+,}. A function carrying at least "
               f"{100 * MOVED_SHARE:g}% of that is marked.", "",
               "| function | parent | commit | change | share | |", "|---|---:|---:|---:|---:|---|"]
        for r in funcs[:SHOWN_FUNCTIONS]:
            md.append(f"| `{r['function']}` | {r['old']:,} | {r['new']:,} | {r['delta']:+,} | "
                      f"{100 * r['share']:.1f}% | {'moved' if r['moved'] else ''} |")
        if len(funcs) > SHOWN_FUNCTIONS:
            md.append(f"| {len(funcs) - SHOWN_FUNCTIONS} more | | | | | |")
        md.append("")
        md.append("All of them: `functions.tsv`.")
    else:
        md.append(cg_note or "No function changed.")

    md += ["", "## The emitted C, parent to first bad commit", ""]
    if changes is None:
        md.append("The C could not be emitted at both commits.")
    elif not changes:
        md.append("The C the two Bends emit for this workload is the same.")
    else:
        md.append("Definitions whose text differs (lines added, removed): " +
                  ", ".join(f"`{n}` (+{p} -{q})" for n, p, q, _ in changes) + ".")
        shown_first = [c for c in changes if c[0] in moved_names] + [c for c in changes if c[0] not in moved_names]
        lines = []
        for _, _, _, diff in shown_first:
            lines += diff
        md += ["", "```diff"] + lines[:DIFF_LINES] + ["```"]
        if len(lines) > DIFF_LINES:
            md.append(f"{len(lines) - DIFF_LINES} more lines in `c.diff`, the whole file's diff.")
        else:
            md.append("The whole file's diff: `c.diff`.")

    md += ["", "## Again", "", "From a clone of this repository (bun, clang and valgrind on PATH):", "", "```sh",
           "make data", f"scripts/count.sh {parent[:12]} {workload}", f"scripts/count.sh {first[:12]} {workload}",
           f"scripts/bisect.sh {workload} {good} {bad} {metric}", "```"]
    if run:
        md += ["", f"The run: {run}."]
    (out / "report.md").write_text("\n".join(md) + "\n")

    kv = {"workload": workload, "metric": metric, "good": good, "good_commit": gr["commit"], "bad": bad,
          "bad_commit": br["commit"], "first_bad": first, "parent": parent, "subject": subject,
          "decided": "no" if candidates else "yes", "candidates": " ".join(candidates),
          "pr": pr_num or "", "pr_title": pr_title or "", "pr_url": pr_url or "", "step_change": step,
          "range_change": range_, "functions_moved": " ".join(moved_names), "c_changed": " ".join(c_names),
          "commits": str(commits or ""), "clang": ", ".join(clang), "valgrind": ", ".join(vg), "run": run or ""}
    with open(out / "report.tsv", "w") as f:
        f.write("key\tvalue\n")
        for k, v in kv.items():
            f.write(f"{k}\t{str(v).replace(chr(9), ' ')}\n")
    return kv


def plan(verdict_tsv):
    """The bisects a release watch verdict asks for: [{"workload", "metrics"}], the metrics that went up (or bits)."""
    out = []
    with open(verdict_tsv) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["verdict"] == "bits":
                out.append({"workload": r["workload"], "metrics": "bits"})
            elif r["verdict"] in ("regression", "mixed"):
                ms = [m for m, lim, col in (("ir", IR_LIMIT, "ir_change"), ("d1", D1_LIMIT, "d1_change"))
                      if r[col] != "-" and float(r[col]) > lim]
                if ms:
                    out.append({"workload": r["workload"], "metrics": " ".join(ms)})
    return out


def issue_section(reports):
    """Markdown naming the first bad commit of each bisect (report.tsv files)."""
    lines = ["## Where it changed", "",
             "Bisected over bendlang/bend's commits between the two releases (`scripts/bisect.sh`, counted the same "
             "way):", ""]
    for p in reports:
        kv = read_tsv_kv(p)
        m = NAMES.get(kv["metric"], kv["metric"])
        pr = f" ([#{kv['pr']}]({kv['pr_url']}) {kv['pr_title']})" if kv.get("pr") else ""
        one = f"- **{kv['workload']}, {m}**: "
        if kv.get("decided") == "no":
            one += f"one of {', '.join(c[:12] for c in kv['candidates'].split())} (skipped commits left)"
        else:
            one += f"{commit_link(kv['first_bad'])}{pr}"
        if kv["metric"] != "bits":
            one += f", {kv['step_change']} at that commit, {kv['range_change']} over the range"
        if kv.get("functions_moved"):
            one += "; moved most: " + ", ".join(f"`{n}`" for n in kv["functions_moved"].split()[:5])
        if kv.get("c_changed"):
            names = kv["c_changed"].split()
            one += "; its C changed in " + ", ".join(f"`{n}`" for n in names[:8]) + \
                (f" and {len(names) - 8} more" if len(names) > 8 else "")
        lines.append(one + ".")
    return lines


def main(argv):
    if not argv:
        print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
        return 2
    cmd, args = argv[0], argv[1:]
    try:
        if cmd == "metrics" and len(args) == 3:
            rows = read_counts(args[0])
            if args[1] not in rows or args[2] not in rows:
                print("bisect_report: no count for an end", file=sys.stderr)
                return 3
            ms = moved(rows[args[1]], rows[args[2]])
            print(" ".join(ms))
            return 0 if ms else 3
        if cmd == "judge" and len(args) == 5:
            counts, metric, good, bad, commit = args
            if metric not in METRICS:
                print(f"bisect_report: no metric {metric}", file=sys.stderr)
                return 2
            v, why = judge(read_counts(counts), metric, good, bad, commit)
            print(f"{v}\t{why}")
            return 0
        if cmd == "report" and args:
            out, rest, opts = args[0], args[1:], {}
            it = iter(rest)
            for a in it:
                if not a.startswith("--"):
                    raise ValueError(f"unexpected argument {a}")
                opts[a[2:].replace("-", "_")] = next(it, "")
            need = ("workload", "metric", "good", "bad", "counts", "first", "parent")
            missing = [k for k in need if not opts.get(k)]
            if missing:
                raise ValueError("report needs --" + ", --".join(missing))
            kv = write_report(out, opts["workload"], opts["metric"], opts["good"], opts["bad"], opts["counts"],
                              opts["first"], opts["parent"], opts.get("subject", ""), opts.get("pr"),
                              opts.get("cg_dir") or "build/count", (opts.get("candidates") or "").split(),
                              opts.get("commits") or None, opts.get("run") or None, opts.get("steps"))
            print(f"{kv['workload']} {kv['metric']}: first bad {kv['first_bad'][:12]}"
                  f"{' (#' + kv['pr'] + ')' if kv['pr'] else ''}, {kv['step_change']} at it, "
                  f"{kv['range_change']} over the range; moved: {kv['functions_moved'] or '-'}")
            return 0
        if cmd == "plan" and len(args) == 1:
            print(json.dumps(plan(args[0])))
            return 0
        if cmd == "issue" and args:
            print("\n".join(issue_section(args)))
            return 0
    except (OSError, KeyError, ValueError) as e:
        print(f"bisect_report: {e}", file=sys.stderr)
        return 2
    print(__doc__.strip().split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
