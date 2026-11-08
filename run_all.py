"""Re-run the complete CISCaRL evidence chain.

Modes
-----
    python run_all.py --dry-run     print every command, run nothing
    python run_all.py --quick       smoke test in a temporary sandbox
    python run_all.py               full canonical re-run (hours)

Options
-------
    --only 23,31,33   run only the listed gates (implies full mode)
    --no-backup       do not copy results/ before a full run
    --no-figures      do not rebuild paper/figs after a full run
    --paper           also rebuild the Word paper from the new figures
    --jobs N          worker count forwarded to gates that accept it

The full run writes into results/ and rewrites the canonical evidence. A
timestamped copy of the old results/ is placed in the system temp directory
first, so nothing is lost if a gate fails halfway.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
RESULTS = ROOT / "results"
DATA = ROOT / "data" / "ACTG175.csv"


# ---------------------------------------------------------------- commands
def notebook_cmd():
    return [PY, "-m", "nbconvert", "--to", "notebook", "--execute",
            "--inplace", str(ROOT / "notebooks" / "CISCaRL_31_steps.ipynb")]


def gate(name, *args):
    return [PY, "-m", f"ciscarl2.{name}", *args]


def full_commands(jobs=None):
    """The exact commands that produced the canonical results."""
    j = ["--jobs", str(jobs)] if jobs is not None else []

    cmds = [
        ("Gate 23  support-constrained selection", gate("gate23", "--reps", "40", *j)),
        ("Gate 28  SCRE head-to-head", gate("gate28", "--reps", "40", *j)),
        ("Gate 30  knob sweep", gate("gate30", "--mode", "sweep", "--reps", "40", *j)),
        ("Gate 30  small-n floor", gate("gate30", "--mode", "smalln", "--reps", "40", *j)),
        ("Gate 30  confirmation", gate("gate30", "--mode", "confirm", "--reps", "40", *j)),
        ("Gate 31  nuisance models", gate("gate31", "--reps", "20", *j)),
        ("Gate 32  rule learners", gate("gate32", "--reps", "20", *j)),
        ("Gate 33  calibration and intervals", gate("gate33", "--reps", "20", *j)),
        ("Gate 33  confirmation block",
         gate("gate33", "--reps", "20", "--start", "921100", "--tag", "confirm", *j)),
        ("Gate 34  cross-fitting folds", gate("gate34", "--reps", "20", *j)),
        ("Gate 35  fairness, SHAP, transport", gate("gate35")),
        ("Gate 36  AIPW vs fixed-horizon TMLE", gate("gate36", "--reps", "20", *j)),
        ("Gate 37  horizon screen", gate("gate37")),
        ("Gate 38  feature selection", gate("gate38")),
        ("Gate 39  learned stacking", gate("gate39", "--reps", "10", *j)),
        ("Gate 40  SCRE alpha path", gate("gate40", "--reps", "10", *j)),
        ("Gate 41  selection-aware intervals", gate("gate41", "--reps", "20", *j)),
        ("Gate 42  horizon grid", gate("gate42")),
        ("Gate 43  horizon inner CV", gate("gate43")),
        ("Gate 44  horizon stability", gate("gate44", *j)),
    ]
    return cmds


def quick_commands():
    """One-rep smoke test of every gate the final paper depends on."""
    return [
        ("Gate 23", gate("gate23", "--reps", "1")),
        ("Gate 28", gate("gate28", "--reps", "1")),
        ("Gate 31", gate("gate31", "--reps", "1", "--models", "cox,rsf",
                         "--rsf-trees", "10", "--gbm-trees", "10")),
        ("Gate 32", gate("gate32", "--reps", "1")),
        ("Gate 33", gate("gate33", "--reps", "1")),
        ("Gate 34", gate("gate34", "--reps", "1")),
        ("Gate 35", gate("gate35")),
        ("Gate 36", gate("gate36", "--reps", "1")),
        ("Gate 37", gate("gate37")),
        ("Gate 38", gate("gate38")),
        ("Gate 39", gate("gate39", "--reps", "1")),
        ("Gate 40", gate("gate40", "--reps", "1")),
        ("Gate 41", gate("gate41", "--reps", "1")),
        ("Gate 42", gate("gate42")),
        ("Gate 43", gate("gate43")),
        ("Gate 44", gate("gate44")),
    ]


# ---------------------------------------------------------------- helpers
def banner(text):
    print("\n" + "=" * 72)
    print(text)
    print("=" * 72, flush=True)


def run(cmds, cwd):
    env = dict(os.environ)
    env["ACTG175_PATH"] = str(cwd / "data" / "ACTG175.csv")
    env["PYTHONPATH"] = str(cwd) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    started = time.time()
    for label, cmd in cmds:
        banner(label)
        print("$", " ".join(cmd), flush=True)
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=cwd, env=env)
        if proc.returncode != 0:
            print(f"\nFAILED: {label} (exit {proc.returncode}) after "
                  f"{time.time() - t0:.1f}s", flush=True)
            return False, label
        print(f"ok: {label} ({time.time() - t0:.1f}s)", flush=True)
    print(f"\nall steps passed in {(time.time() - started) / 60:.1f} min")
    return True, None


def backup_results():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = Path(tempfile.gettempdir()) / f"ciscarl_results_backup_{stamp}"
    shutil.copytree(RESULTS, dest)
    print(f"backup of results/ -> {dest}")
    return dest


def sandbox():
    """Copy code and data to a temp tree so --quick cannot touch evidence."""
    tmp = Path(tempfile.mkdtemp(prefix="ciscarl_quick_"))
    shutil.copytree(ROOT / "ciscarl2", tmp / "ciscarl2",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (tmp / "data").mkdir()
    shutil.copy2(DATA, tmp / "data" / "ACTG175.csv")
    (tmp / "results").mkdir()
    print(f"quick sandbox -> {tmp}")
    return tmp


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", help="print commands only")
    g.add_argument("--quick", action="store_true", help="sandbox smoke test")
    ap.add_argument("--only", default="", help="comma-separated gate numbers")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--paper", action="store_true")
    ap.add_argument("--jobs", type=int, default=None)
    args = ap.parse_args(argv)

    if not DATA.exists():
        raise SystemExit(f"missing dataset: {DATA}")

    if args.quick:
        cmds = quick_commands()
        target = sandbox()
        ok, failed = run(cmds, target)
        print(f"\nquick sandbox kept for inspection: {target}")
        return 0 if ok else 1

    cmds = full_commands(args.jobs)
    if args.only:
        wanted = {s.strip() for s in args.only.split(",") if s.strip()}
        def gate_number(cmd):
            return cmd[2].rsplit("gate", 1)[-1]
        cmds = [(label, cmd) for label, cmd in cmds
                if gate_number(cmd).split(".")[0] in wanted]
        if not cmds:
            raise SystemExit(f"--only {args.only} matched no gate")

    if args.dry_run:
        banner("run_all --dry-run")
        for label, cmd in cmds:
            print(f"{label}: {' '.join(cmd)}")
        if not args.only:
            print(f"notebook: {' '.join(notebook_cmd())}")
        if not args.no_figures and not args.only:
            print(f"figures : {PY} paper/make_paper_figures.py")
        if args.paper and not args.only:
            print(f"paper   : {PY} paper/build_ieee_detailed.py")
        return 0

    if not args.no_backup and RESULTS.exists():
        backup_results()

    ok, failed = run(cmds, ROOT)
    if not ok:
        return 1

    if not args.only:
        banner("notebook")
        env = dict(os.environ)
        env["ACTG175_PATH"] = str(DATA)
        env["PYTHONIOENCODING"] = "utf-8"
        if subprocess.run(notebook_cmd(), cwd=ROOT, env=env).returncode != 0:
            print("FAILED: notebook execution")
            return 1
        print("ok: notebook")

    if not args.no_figures and not args.only:
        banner("paper figures")
        if subprocess.run([PY, str(ROOT / "paper" / "make_paper_figures.py")],
                          cwd=ROOT).returncode != 0:
            print("FAILED: figure generation")
            return 1
        print("ok: figures")

    if args.paper and not args.only:
        banner("Word paper")
        if subprocess.run([PY, str(ROOT / "paper" / "build_ieee_detailed.py")],
                          cwd=ROOT).returncode != 0:
            print("FAILED: paper build")
            return 1
        print("ok: paper docx (PDF export needs Microsoft Word)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
