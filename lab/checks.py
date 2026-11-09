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
Investigations 07, 08 and 09 keep their results, cases and findings private (they carry plant text) and publish a
counts-only `receipt.json`, derived by code (`python3 -I check.py --receipt` in the investigation). They are checked in two
modes. Private checkout (results present): the receipt must equal a fresh derivation, then the investigation's own
`check.py` re-derives findings.md (07: derive + compare; 08: re-replays the case set through the rule; 09: re-runs the
redactor against the key and ties each sit to its inputs). Public checkout (results absent): only the receipt is there.
In both modes every k/n or two-decimal number in the docs/INDEX.md row and in the result cell of the LESSONS.md row must
be one the receipt carries, and the INDEX row must carry at least one (operator decision 2026-11-09: counts public,
cases private).
Investigation 02's `check.py` (no number posted yet: asserts the case-set freeze and shape) is wired the same way.
08b (ten legitimate writes, same directory as 08) has `check_08b.py`, wired the same way; it posts no number in INDEX.
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


_RATIO = re.compile(r"(\d+)\s*(?:/|of)\s*(\d+)")
_DECIMAL = re.compile(r"(?<![\d.])0\.\d{2}(?!\d)")


def _receipt_tokens(obj, out: set) -> set:
    """Every [k, n] pair in the receipt as 'k/n', 'k of n' and its two-decimal fraction; every bare int as itself."""
    if isinstance(obj, list) and len(obj) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in obj):
        k, n = obj
        out.update({f"{k}/{n}", f"{k} of {n}"})
        if n:
            out.add(f"{k / n:.2f}")
    elif isinstance(obj, dict):
        for v in obj.values():
            _receipt_tokens(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _receipt_tokens(v, out)
    elif isinstance(obj, int) and not isinstance(obj, bool):
        out.add(str(obj))
    return out


def _row_numbers(cell: str) -> list[str]:
    nums = [f"{m.group(1)}/{m.group(2)}" for m in _RATIO.finditer(cell)]
    return nums + _DECIMAL.findall(cell)


def _public_rows_drift(num: str, rec: dict, root: Path) -> list[str]:
    """The INDEX row and the LESSONS result cell may only carry numbers the receipt carries."""
    allowed = _receipt_tokens(rec, set())
    drift = []
    index = (root / "docs" / "INDEX.md").read_text()
    m = re.search(rf"^\| {num} \|.*$", index, re.M)
    if not m:
        return [f"INDEX: no {num} row"]
    nums = _row_numbers(m.group(0))
    if not nums:
        drift.append(f"INDEX {num} row carries no count; receipt.json has them")
    for x in nums:
        if x not in allowed and x.replace("/", " of ") not in allowed:
            drift.append(f"INDEX {num} row carries {x}, which receipt.json does not re-derive")
    lessons = (root / "LESSONS.md").read_text() if (root / "LESSONS.md").exists() else ""
    m = re.search(rf"^\| {num} .*$", lessons, re.M)
    if m:
        cells = [c.strip() for c in m.group(0).strip().strip("|").split("|")]
        if len(cells) >= 3:
            for x in _row_numbers(cells[2]):
                if x not in allowed and x.replace("/", " of ") not in allowed:
                    drift.append(f"LESSONS {num} result cell carries {x}, which receipt.json does not re-derive")
    return drift


def _check_receipted(num: str, inv_dir: str, verbose: bool, root: Path) -> list[str]:
    inv = root / "investigations" / inv_dir
    rec_path = inv / "receipt.json"
    if not rec_path.exists():
        return [f"{num}: no receipt.json at {rec_path.relative_to(root)}"]
    rec = json.loads(rec_path.read_text())
    drift = []
    private = (inv / "results").exists() and (inv / "check.py").exists()
    if private:
        spec = importlib.util.spec_from_file_location(f"inv{num}_check", inv / "check.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fresh = json.loads(json.dumps(mod.receipt(root), ensure_ascii=False))
        if fresh != rec:
            diff = sorted(k for k in set(fresh) | set(rec) if fresh.get(k) != rec.get(k))
            drift.append(f"{num} receipt.json differs from a fresh derivation in {diff}")
        drift += mod.check(root, verbose=verbose)
    elif verbose:
        print(f"  {num} results private, absent here: checked the INDEX and LESSONS rows against receipt.json")
    drift += _public_rows_drift(num, rec, root)
    if verbose and not any(d.startswith(("INDEX", "LESSONS")) for d in drift):
        print(f"  {num} INDEX row and LESSONS result cell: every count re-derives from receipt.json")
    return drift


def check_07(verbose: bool = True, root: Path = ROOT) -> list[str]:
    return _check_receipted("07", "07-injection-hosted", verbose, root)


def check_08(verbose: bool = True, root: Path = ROOT) -> list[str]:
    return _check_receipted("08", "08-confirm-on-mutate", verbose, root)


def check_08b(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """08b lives in 08's private directory; no published file may carry an 08b number. Both modes assert that the INDEX
    08b row has none; the private checkout also re-replays the recording and re-derives findings-08b.md."""
    inv = root / "investigations" / "08-confirm-on-mutate"
    if not (inv / "check_08b.py").exists():
        index = (root / "docs" / "INDEX.md").read_text()
        m = re.search(r"^\| 08b \|.*$", index, re.M)
        hits = re.findall(r"\d+\s*(?:/|of)\s*\d+", m.group(0)) if m else []
        if verbose:
            print("  08b results private, absent here: only checked that the INDEX 08b row carries no number")
        return ([] if m else ["INDEX: no 08b row"]) + ([f"INDEX 08b row carries {hits} with no results to re-derive them"] if hits else [])
    spec = importlib.util.spec_from_file_location("inv08b_check", inv / "check_08b.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, verbose=verbose)


def check_09(verbose: bool = True, root: Path = ROOT) -> list[str]:
    return _check_receipted("09", "09-pii-redaction", verbose, root)


def check_02(verbose: bool = True, root: Path = ROOT) -> list[str]:
    """02's case set holds plant text, so it stays private; no published file may carry an 02 number. Nothing is posted
    yet: the private checkout asserts the case-set freeze (sha256 block in question.md) and its shape; both modes assert
    that the INDEX 02 row carries no k/n."""
    inv = root / "investigations" / "02-memory-poisoning"
    if not (inv / "check.py").exists():
        index = (root / "docs" / "INDEX.md").read_text()
        m = re.search(r"^\| 02 \|.*$", index, re.M)
        hits = re.findall(r"\d+\s*(?:/|of)\s*\d+", m.group(0)) if m else []
        if verbose:
            print("  02 case set private, absent here: only checked that the INDEX 02 row carries no number")
        return ([] if m else ["INDEX: no 02 row"]) + ([f"INDEX 02 row carries {hits} with no results to re-derive them"] if hits else [])
    spec = importlib.util.spec_from_file_location("inv02_check", inv / "check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(root, verbose=verbose)


CHECKS = {"01": check_01, "02": check_02, "05": check_05, "07": check_07, "08": check_08, "08b": check_08b, "09": check_09}
