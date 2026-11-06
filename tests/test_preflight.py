"""scripts/preflight.sh on a fake machine: /sys and /proc trees of its own, and stand-ins for ps, powerprofilesctl and
sleep (which moves /proc/stat on, as if the sample's second had passed). An idle machine passes; each busy check alone
fails it and is named."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from synth import ROOT

IDLE_PS = "    1 systemd /sbin/init\n  200 foot foot\n"
# cpu3 and its sibling cpu4: user nice system idle iowait irq softirq steal
STAT0 = "cpu3 100 0 0 1000 0 0 0 0\ncpu4 100 0 0 1000 0 0 0 0\n"
STAT_IDLE = "cpu3 101 0 0 1099 0 0 0 0\ncpu4 101 0 0 1099 0 0 0 0\n"   # 1% busy
STAT_BUSY = "cpu3 101 0 0 1099 0 0 0 0\ncpu4 150 0 0 1050 0 0 0 0\n"   # 50% busy


class Preflight(unittest.TestCase):
    def run_pf(self, *args, ps=IDLE_PS, profile="performance", load="0.20", online="1", paranoid="1",
               siblings="3-4", after=STAT_IDLE, load_after=None, cpu=None, before=STAT0, pids=None, extra=None):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            sys_, proc, bin_ = d / "sys", d / "proc", d / "bin"
            for s, t, o in (("ADP1", "Mains", online), ("BAT1", "Battery", None)):
                (sys_ / "class" / "power_supply" / s).mkdir(parents=True)
                (sys_ / "class" / "power_supply" / s / "type").write_text(t + "\n")
                if o is not None:
                    (sys_ / "class" / "power_supply" / s / "online").write_text(o + "\n")
            topo = sys_ / "devices" / "system" / "cpu" / f"cpu{cpu or 3}" / "topology"
            topo.mkdir(parents=True)
            (topo / "thread_siblings_list").write_text(siblings + "\n")
            (proc / "sys" / "kernel").mkdir(parents=True)
            (proc / "sys" / "kernel" / "perf_event_paranoid").write_text(paranoid + "\n")
            (proc / "loadavg").write_text(f"{load} 0.10 0.10 1/100 1000\n")
            (proc / "stat").write_text(before)
            (proc / "stat.after").write_text(after)
            # pid: (ppid, ticks before the sample, ticks after), as /proc/<pid>/stat's utime (stime 0)
            for pid, (ppid, t0, t1) in (pids or {}).items():
                (proc / str(pid)).mkdir()
                for f, t in (("stat", t0), ("stat.after", t1)):
                    (proc / str(pid) / f).write_text(f"{pid} (x y) S {ppid} 0 0 0 0 0 0 0 0 0 {t} 0 0 0 0\n")
            bin_.mkdir()
            for name, body in (("ps", f"cat <<'EOF'\n{ps}EOF\n"), ("powerprofilesctl", (f"echo '{load_after} 0.10 0.10 1/100 1000' > '{proc}/loadavg'\n"
                                                     if load_after else "") + f"echo {profile}\n"),
                               ("sleep", f"cp '{proc}/stat.after' '{proc}/stat'\n"
                                         f"for f in '{proc}'/[0-9]*/stat.after; do [ -f \"$f\" ] && cp \"$f\" \"${{f%.after}}\"; done\n")):
                (bin_ / name).write_text("#!/bin/sh\n" + body)
                (bin_ / name).chmod(0o755)
            env = dict(os.environ, PREFLIGHT_SYS=str(sys_), PREFLIGHT_PROC=str(proc), PREFLIGHT_SAMPLE="1",
                       PATH=f"{bin_}:{os.environ['PATH']}")
            env.pop("CPU", None)
            env.pop("AGENTS_IDLE_OK", None)
            env.update(extra or {})
            if cpu:
                env["CPU"] = cpu
            return subprocess.run(["bash", str(ROOT / "scripts" / "preflight.sh"), *args], env=env,
                                  capture_output=True, text=True, timeout=30)

    def test_an_idle_machine_passes(self):
        p = self.run_pf()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("preflight: idle, fit for timings", p.stdout)
        self.assertIn("ok     cpu3_sibling         cpu4 1%", p.stdout)

    def test_each_busy_check_fails_it(self):
        for kw, name in ((dict(online="0"), "ac"), (dict(profile="balanced"), "power_profile"),
                         (dict(load="2.50"), "loadavg"), (dict(paranoid="2"), "perf_event_paranoid"),
                         (dict(after=STAT_BUSY), "cpu3_sibling"),
                         (dict(ps=IDLE_PS + "  300 opencode opencode serve\n"), "other_processes"),
                         (dict(ps=IDLE_PS + "  301 claude claude\n"), "other_processes"),
                         (dict(ps=IDLE_PS + "  302 codex codex app-server\n"), "other_processes"),
                         (dict(ps=IDLE_PS + "  303 bend bend main.bend -o x\n"), "other_processes"),
                         (dict(ps=IDLE_PS + "  304 bun bun /src/bend2/main.ts main.bend\n"), "other_processes")):
            with self.subTest(name=name, **kw):
                p = self.run_pf(**kw)
                self.assertEqual(p.returncode, 1, p.stdout)
                self.assertIn(f"preflight: busy ({name})", p.stdout)

    def test_idle_agents_pass_with_agents_idle_ok(self):
        # one tick of claude's tree over the one-second sample: 1% of a CPU at 100 ticks a second, under 2%
        p = self.run_pf(ps=IDLE_PS + "  301 claude claude\n", pids={301: (1, 1000, 1001)}, extra={"AGENTS_IDLE_OK": "1"})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("ok     other_processes      claude x1, agents idle 1.0%", p.stdout)

    def test_an_agents_descendant_counts(self):
        # a build the agent runs (pid 400, its child) is in its tree: 21 ticks, 21%
        p = self.run_pf(ps=IDLE_PS + "  301 claude claude\n  400 make make check\n",
                        pids={301: (1, 1000, 1001), 400: (301, 500, 520), 200: (1, 10, 90)},
                        extra={"AGENTS_IDLE_OK": "1"})
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("busy   other_processes      claude x1, agents 21.0%", p.stdout)

    def test_a_compiler_is_busy_even_with_agents_idle_ok(self):
        p = self.run_pf(ps=IDLE_PS + "  301 claude claude\n  303 bend bend main.bend -o x\n",
                        pids={301: (1, 1000, 1000)}, extra={"AGENTS_IDLE_OK": "1"})
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("preflight: busy (other_processes)", p.stdout)
        self.assertNotIn("agents", p.stdout)

    def test_the_load_is_read_before_the_other_checks(self):
        # the checks' own processes (here powerprofilesctl) must not count in the load average they judge
        p = self.run_pf(load="0.40", load_after="2.50")
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("ok     loadavg              0.40", p.stdout)

    def test_the_processes_are_named(self):
        p = self.run_pf(ps=IDLE_PS + "  300 opencode opencode\n  301 opencode opencode\n")
        self.assertIn("busy   other_processes      opencode x2", p.stdout)

    def test_no_sibling_and_no_battery_pass(self):
        p = self.run_pf(siblings="3")
        self.assertIn("ok     cpu3_sibling         none", p.stdout)

    def test_cpu_names_the_core_whose_sibling_is_sampled(self):
        # CPU=5 (run.sh's pin): its sibling cpu6 is sampled, and the check is named after it
        before, after = (t.replace("cpu3", "cpu5").replace("cpu4", "cpu6") for t in (STAT0, STAT_BUSY))
        p = self.run_pf(cpu="5", siblings="5-6", before=before, after=after)
        self.assertEqual(p.returncode, 1, p.stdout)
        self.assertIn("busy   cpu5_sibling         cpu6 50%", p.stdout)
        self.assertNotIn("cpu3", p.stdout)

    def test_env_lines_for_run_sh(self):
        p = self.run_pf("--env", load="3.00")
        self.assertEqual(p.returncode, 0)
        lines = dict(l.split("\t") for l in p.stdout.splitlines())
        self.assertEqual(lines["pre_loadavg"], "3.00")
        self.assertEqual(lines["pre_ac"], "online")
        self.assertEqual(lines["busy"], "loadavg")
        self.assertEqual(dict(l.split("\t") for l in self.run_pf("--env").stdout.splitlines())["busy"], "no")


if __name__ == "__main__":
    unittest.main()
