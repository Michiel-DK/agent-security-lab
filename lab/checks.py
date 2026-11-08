"""`lab check`: re-derive posted numbers from committed results. No API key, no model call, no GPU.

One entry per investigation in CHECKS. An investigation without an entry has no posted number to check.
Each check returns a list of drift messages (empty = every posted number re-derives) and prints what it compared.

Investigation 01 is checked three ways:
  1. the stored `summary` in each results file is recomputed from its `records` and the committed
     `dataset/cases.jsonl` with run.py's own `summarize()` and must match exactly;
  2. every cell of the tables in `findings.md` (Opus aggregate, Opus per-case, gemma) must be a correct
     two-decimal rounding of the recomputed value;
  3. the 01 row of `docs/INDEX.md` must quote the same numbers.
Not checked: numbers in findings.md's prose ("Reading"), README's Lab section and SHOWCASE.md; they copy table cells.
Investigation 05 has its own `check.py`; it is run as a subprocess and its exit code is the verdict.
Investigation 07 has its own `check.py` (derive + compare); it is imported and given the repo root, so tests can point it
at a tampered copy.
Investigation 08 has its own `check.py` (re-replays the case set through the rule, then compares the counts); it is
imported and given the repo root the same way. Investigation 09's `check.py` (re-runs the redactor against the key,
ties each sit to its inputs, re-derives the pass counts) is wired the same way.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INV = ROOT / "investigations"

# A posted two-decimal cell matches a stored value v when |posted - v| <= 0.005. That accepts either
# rounding at an exact tie (findings.md's per-case table rounds 0.125 to 0.12, its aggregate table rounds
# 0.625 to 0.63) and rejects anything else.
TOL = 0.005 + 1e-9


def _load_run01(inv: Path):
    spec = importlib.util.spec_from_file_location("inv01_run", inv / "01-cve-localization" / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _num(cell: str) -> float:
    c = cell.strip().strip("*").strip()
    if c.endswith("%"):
        return float(c[:-1]) / 100
    return float(c)


def _table(text: str, header_start: str) -> list[list[str]]:
    """Rows (cells stripped) of the first markdown table whose header line starts with `header_start`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith(header_start):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                rows.append([c.strip() for c in row.strip().strip("|").split("|")])
            return rows
    raise ValueError(f"no table starting {header_start!r}")


AGG_COLS = ["cases", "pass_at_k_case_hit_rate", "mean_single_pass_recall", "mean_union_recall",
            "post_fpr_fixed_fn", "post_any_flag_rate", "mean_candidates_per_pre_call"]


def _split_key(label: str) -> str:
    label = label.strip("*").strip()
    if label == "all":
        return "all"
    m = re.match(r"(cutoff|tier) = (\w+)", label)
    if not m:
        raise ValueError(f"unknown split label {label!r}")
    return f"{m.group(1)}={m.group(2)}"


def _cmp(drift: list[str], where: str, posted: float, got, integer: bool = False) -> None:
    if got is None:
        drift.append(f"{where}: posted {posted}, results have no value")
    elif integer and int(posted) != int(got):
        drift.append(f"{where}: posted {int(posted)}, results derive {got}")
    elif not integer and abs(posted - float(got)) > TOL:
        drift.append(f"{where}: posted {posted}, results derive {got}")


def check_01(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """`root` is the repo root; tests point it at a tampered copy."""
    d01 = root / "investigations" / "01-cve-localization"
    run = _load_run01(root / "investigations")
    cases = run.load_cases()  # LAB_ONLY must be unset; checked below via the case count
    drift: list[str] = []
    files = sorted((d01 / "results").glob("*.json"))
    derived = {}
    for f in files:
        data = json.loads(f.read_text())
        if len(cases) != data["n_cases"]:
            drift.append(f"{f.name}: n_cases {data['n_cases']} but dataset has {len(cases)} (LAB_ONLY set?)")
            continue
        got = run.summarize(cases, data["records"])
        # json round-trip so tuples/ints compare as the stored file does
        got = json.loads(json.dumps(got))
        if got != data["summary"]:
            bad = [k for k in got["aggregate"] if got["aggregate"][k] != data["summary"]["aggregate"].get(k)]
            bad += [k for k in got["per_case"] if got["per_case"][k] != data["summary"]["per_case"].get(k)]
            drift.append(f"{f.name}: stored summary does not re-derive from records (differs at {bad[:5]})")
        derived[f.name] = (got, data["records"])
        if verbose:
            print(f"  01 {f.name}: summary re-derived from {len(data['records'])} records")

    text = (d01 / "findings.md").read_text()
    opus = next((v for k, v in derived.items() if "opus" in k), None)
    gemma = next((v for k, v in derived.items() if "gemma" in k), None)
    n = 0
    if opus is None or gemma is None:
        drift.append("01: Opus or gemma results file missing")
        return drift
    agg = opus[0]["aggregate"]
    for row in _table(text, "| split |"):
        key = _split_key(row[0])
        for col, cell in zip(AGG_COLS, row[1:]):
            _cmp(drift, f"01 findings Opus {key} {col}", _num(cell), agg[key][col], integer=(col == "cases"))
            n += 1
    pc = opus[0]["per_case"]
    for row in _table(text, "| case | truth |"):
        cid = row[0]
        if cid not in pc:
            drift.append(f"01 findings per-case: {cid} not in results")
            continue
        _cmp(drift, f"01 findings {cid} single-pass", _num(row[2]), pc[cid]["mean_pass_recall"])
        _cmp(drift, f"01 findings {cid} union", _num(row[3]), pc[cid]["union_recall"])
        _cmp(drift, f"01 findings {cid} flagged-fixed", _num(row[4]), pc[cid]["post_flagged_fixed_passes"], integer=True)
        n += 3

    g_agg, g_rec = gemma[0]["aggregate"]["cutoff=post"], gemma[1]
    g_counts = {
        "calls with the file truncated": (sum(1 for r in g_rec if r.get("truncated")), len(g_rec)),
        "calls with parseable JSON": (sum(1 for r in g_rec if r.get("parsed")), len(g_rec)),
        "pre-patch calls naming nothing": (sum(1 for r in g_rec if r["variant"] == "pre" and not r.get("predicted")),
                                           sum(1 for r in g_rec if r["variant"] == "pre")),
    }
    g_rates = {
        "pass@4 case hit rate": "pass_at_k_case_hit_rate", "single-pass recall": "mean_single_pass_recall",
        "union recall": "mean_union_recall", "post-patch FPR on fixed functions": "post_fpr_fixed_fn",
        "flags anything on clean file": "post_any_flag_rate", "candidates per pre-patch call": "mean_candidates_per_pre_call",
    }
    for row in _table(text, "| metric (post-cutoff, n = 20) |"):
        label, cell = row[0], row[1]
        if label in g_rates:
            _cmp(drift, f"01 findings gemma {label}", _num(cell), g_agg[g_rates[label]])
        elif label in g_counts:
            a, b = (int(x) for x in cell.split("/"))
            if (a, b) != g_counts[label]:
                drift.append(f"01 findings gemma {label}: posted {a}/{b}, results derive {g_counts[label][0]}/{g_counts[label][1]}")
        else:
            drift.append(f"01 findings gemma: unknown row {label!r}")
        n += 1

    # docs/INDEX.md, row 01: the numbers it quotes, each with the value it must equal
    index_row = next(l for l in (root / "docs" / "INDEX.md").read_text().splitlines() if l.startswith("| 01 |"))
    post, named, mech = agg["cutoff=post"], agg["tier=named"], agg["tier=mechanism"]
    claims = [
        (r"(\d+) cases, (\d+) post-cutoff", [len(cases), post["cases"]], True),
        (r"single-pass recall (\d+(?:\.\d+)?)", [post["mean_single_pass_recall"]], False),
        (r"union (\d+(?:\.\d+)?)", [post["mean_union_recall"]], False),
        (r"post-patch FPR (\d+(?:\.\d+)?)", [post["post_fpr_fixed_fn"]], False),
        (r"flags something on (\d+)%", [post["post_any_flag_rate"] * 100], False),
        (r"Named-function cases (\d+(?:\.\d+)?) / FPR (\d+(?:\.\d+)?)", [named["mean_single_pass_recall"], named["post_fpr_fixed_fn"]], False),
        (r"mechanism cases (\d+(?:\.\d+)?) / FPR (\d+(?:\.\d+)?)", [mech["mean_single_pass_recall"], mech["post_fpr_fixed_fn"]], False),
        (r"gemma4-e4b: recall (\d+(?:\.\d+)?)", [gemma[0]["aggregate"]["cutoff=post"]["mean_single_pass_recall"]], False),
    ]
    for pat, want, integer in claims:
        m = re.search(pat, index_row)
        if not m:
            drift.append(f"01 INDEX: pattern {pat!r} not found in the 01 row")
            continue
        for posted, got in zip(m.groups(), want):
            tol_scale = 100 if "%" in pat else 1
            if integer:
                _cmp(drift, f"01 INDEX {pat}", float(posted), got, integer=True)
            elif abs(float(posted) - got) > TOL * tol_scale:
                drift.append(f"01 INDEX {pat}: posted {posted}, results derive {got}")
            n += 1
    if verbose:
        print(f"  01 compared {n} posted cells (findings.md tables + INDEX row) with the re-derived values")
    return drift


def check_05(verbose: bool = True) -> list[str]:
    p = subprocess.run([sys.executable, "-I", str(INV / "05-model-comparison" / "check.py")],
                       capture_output=True, text=True, cwd=INV / "05-model-comparison")
    if verbose:
        tail = (p.stdout.strip().splitlines() or [""])[-1]
        print(f"  05 check.py exit {p.returncode}: {tail}")
    if p.returncode != 0:
        return [f"05 check.py exit {p.returncode}:\n{p.stdout[-2000:]}{p.stderr[-2000:]}"]
    return []


def check_07(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """07's results and findings are private (they hold planted text), so no published file may carry a 07 number.
    Both modes assert that the INDEX 07 row has none; the private checkout also re-derives findings.md."""
    inv = root / "investigations" / "07-injection-hosted"
    if not inv.exists():
        index = (root / "docs" / "INDEX.md").read_text()
        m = re.search(r"^\| 07 \|.*$", index, re.M)
        hits = re.findall(r"\d+/\d+", m.group(0)) if m else []
        if verbose:
            print("  07 results private, absent here: only checked that the INDEX 07 row carries no number")
        return ([] if m else ["INDEX: no 07 row"]) + ([f"INDEX 07 row carries {hits} with no results to re-derive them"] if hits else [])
    spec = importlib.util.spec_from_file_location("inv07_check", inv / "check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, verbose=verbose)


def check_08(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """08's case set holds planted text, so it stays private; no published file may carry an 08 number.
    Both modes assert that the INDEX 08 row has none; the private checkout also re-replays and re-derives findings.md."""
    inv = root / "investigations" / "08-confirm-on-mutate"
    if not inv.exists():
        index = (root / "docs" / "INDEX.md").read_text()
        m = re.search(r"^\| 08 \|.*$", index, re.M)
        hits = re.findall(r"\d+\s*(?:/|of)\s*\d+", m.group(0)) if m else []
        if verbose:
            print("  08 results private, absent here: only checked that the INDEX 08 row carries no number")
        return ([] if m else ["INDEX: no 08 row"]) + ([f"INDEX 08 row carries {hits} with no results to re-derive them"] if hits else [])
    spec = importlib.util.spec_from_file_location("inv08_check", inv / "check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, verbose=verbose)


def check_09(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """09's corpus holds the exam's inputs (including their planted-instruction text), so it stays private; no published
    file may carry a 09 number. Both modes assert that the INDEX 09 row has none; the private checkout also re-runs the
    redactor against the key, ties every sit to its inputs, and re-derives findings.md."""
    inv = root / "investigations" / "09-pii-redaction"
    spec = importlib.util.spec_from_file_location("inv09_check", inv / "check.py") if (inv / "check.py").exists() else None
    if spec is None:
        index = (root / "docs" / "INDEX.md").read_text()
        m = re.search(r"^\| 09 \|.*$", index, re.M)
        hits = re.findall(r"\d+\s*(?:/|of)\s*\d+", m.group(0)) if m else []
        if verbose:
            print("  09 results private, absent here: only checked that the INDEX 09 row carries no number")
        return ([] if m else ["INDEX: no 09 row"]) + ([f"INDEX 09 row carries {hits} with no results to re-derive them"] if hits else [])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, verbose=verbose)


CHECKS = {"01": check_01, "05": check_05, "07": check_07, "08": check_08, "09": check_09}
