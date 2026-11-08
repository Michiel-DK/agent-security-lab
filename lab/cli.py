"""`python3 -m lab check|diff|run`. Shape from lab-template; `check` dispatches per investigation (lab/checks.py)."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from . import checks

ROOT = Path(__file__).resolve().parents[1]


def _prediction_committed(name):
    p = ROOT / "predictions" / f"{name}.md"
    if not p.exists():
        return False, f"no predictions/{name}.md"
    text = p.read_text()
    if "## Prediction" not in text or "## Mechanism" not in text:
        return False, f"predictions/{name}.md needs '## Prediction' and '## Mechanism'"
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(p)], capture_output=True, cwd=ROOT)
    if tracked.returncode != 0:
        return False, f"predictions/{name}.md is not tracked by git"
    dirty = subprocess.run(["git", "status", "--porcelain", str(p)], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    if dirty:
        return False, f"predictions/{name}.md has uncommitted edits"
    return True, ""


DIFF_KEYS = ["mean_single_pass_recall", "mean_union_recall", "post_fpr_fixed_fn", "post_any_flag_rate"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="lab")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="re-derive the posted numbers from committed results; exit 1 on drift")
    c.add_argument("ids", nargs="*", help=f"investigation ids (default: all of {sorted(checks.CHECKS)})")
    d = sub.add_parser("diff", help="investigation-01-shaped results files: b - a on the cutoff=post aggregate")
    d.add_argument("a"); d.add_argument("b")
    r = sub.add_parser("run", help="produce a NEW results file; refuses without a committed prediction")
    r.add_argument("method"); r.add_argument("--name", required=True)
    a = p.parse_args(argv)
    if a.cmd == "check":
        ids = a.ids or sorted(checks.CHECKS)
        unknown = [i for i in ids if i not in checks.CHECKS]
        if unknown:
            print(f"no check registered for {unknown}; registered: {sorted(checks.CHECKS)}", file=sys.stderr)
            return 2
        rc = 0
        for i in ids:
            drift = checks.CHECKS[i]()
            for msg in drift:
                print(f"DRIFT {msg}")
            print(f"{i}: {'OK, every checked cell re-derives' if not drift else f'{len(drift)} drift(s)'}")
            rc = rc or (1 if drift else 0)
        return rc
    if a.cmd == "diff":
        ra = json.load(open(a.a))["summary"]["aggregate"]["cutoff=post"]
        rb = json.load(open(a.b))["summary"]["aggregate"]["cutoff=post"]
        for k in DIFF_KEYS:
            print(f"{k:28s} {rb[k] - ra[k]:+.3f}  ({ra[k]} -> {rb[k]})")
        return 0
    if a.cmd == "run":
        ok, why = _prediction_committed(a.name)
        if not ok:
            print(f"refused: {why}", file=sys.stderr)
            return 2
        print(f"run: method '{a.method}' has no runner wired into lab/ yet; the lane that owns it adds one and writes a new "
              f"results file (never overwrites), recording the prediction commit", file=sys.stderr)
        return 3
    return 1
