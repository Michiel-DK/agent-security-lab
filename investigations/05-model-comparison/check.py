#!/usr/bin/env python3
"""Re-derive every number posted in findings.md from the committed results.

    python3 -I check.py

Stdlib only. No API key, no model calls, no GPU. Reads the four
../01-cve-localization/results/*.json files, prints the tables that
findings.md posts, and compares each printed cell with the EXPECTED values
below (copied from findings.md). Exit 1 on any drift > 0.01 (or on any
integer-count mismatch), printing the cell. Exit 0 otherwise.

Rounding: two decimals, half-up, applied to the value as stored in the
results file (which run.py already stores at three decimals). Python's
round() is half-to-even on binary floats (round(0.425, 2) == 0.42); this
script uses decimal.ROUND_HALF_UP on str(value) instead, so 0.425 -> 0.43.

The gemma row is printed for context and marked "not comparable" (truncated
files, half the replies without JSON). Its cells are checked as warnings only;
the kill clause does not apply to it.
"""
from __future__ import annotations

import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "01-cve-localization" / "results"
CASES = HERE.parent / "01-cve-localization" / "dataset" / "cases.jsonl"

FILES = {
    "Opus 5.5": "claude_claude-opus-5-5_20261023T202745Z.json",
    "Sonnet 5.5": "claude_claude-sonnet-5-5_20261023T210536Z.json",
    "Haiku 5.5": "claude_claude-haiku-5-5_20261023T204954Z.json",
}
GEMMA = ("gemma4-e4b-ctx16k", "ollama_gemma4-e4b-ctx16k_latest_20261023T222005Z.json")
CLAUDE = list(FILES)
MAX_TOKENS = 2048  # lab/models.py max_tokens for the claude backend

COLS = [  # (header, summary.aggregate key)
    ("cases", "cases"),
    ("pass@4 hit", "pass_at_k_case_hit_rate"),
    ("single-pass recall", "mean_single_pass_recall"),
    ("union recall", "mean_union_recall"),
    ("post FPR (fixed fn)", "post_fpr_fixed_fn"),
    ("post any-flag", "post_any_flag_rate"),
    ("cand/call", "mean_candidates_per_pre_call"),
]

# ---- expected values: these are the cells posted in findings.md ----------
EXPECTED = {
    "cutoff=post": {
        "Opus 5.5":   [20, 0.65, 0.21, 0.43, 0.30, 0.84, 0.74],
        "Sonnet 5.5": [20, 0.65, 0.33, 0.43, 0.43, 0.94, 1.09],
        "Haiku 5.5":  [20, 0.70, 0.34, 0.45, 0.29, 0.51, 0.91],
    },
    "tier=named": {
        "Opus 5.5":   [8, 0.75, 0.47, 0.66, 0.13, 0.75, 0.88],
        "Sonnet 5.5": [8, 0.63, 0.44, 0.56, 0.09, 0.84, 1.19],
        "Haiku 5.5":  [8, 0.63, 0.44, 0.53, 0.16, 0.50, 0.97],
    },
    "tier=mechanism": {
        "Opus 5.5":   [12, 0.58, 0.09, 0.31, 0.40, 0.85, 0.69],
        "Sonnet 5.5": [12, 0.67, 0.25, 0.38, 0.50, 0.94, 1.06],
        "Haiku 5.5":  [12, 0.67, 0.19, 0.35, 0.25, 0.50, 0.77],
    },
}
# post-cutoff reply health, per model: [post-patch calls, of which no JSON
# (empty or unparsable), of which hit max_tokens; pre-patch no-JSON, of which
# hit max_tokens; any-flag rate among post-patch replies that did parse]
EXPECTED_HEALTH = {
    "Opus 5.5":   [80, 1, 1, 5, 5, 0.85],
    "Sonnet 5.5": [80, 0, 0, 0, 0, 0.94],
    "Haiku 5.5":  [80, 28, 28, 14, 14, 0.79],
}
# post-cutoff case agreement: case -> (tier, hits O/S/H as 1/0, post flagged-fixed passes O/S/H)
EXPECTED_CASES = {
    "php2shell-session-rfc1867":   ("mechanism", (1, 1, 1), (1, 2, 3)),
    "php2shell-opcache-persist":   ("named",     (0, 0, 0), (0, 2, 0)),
    "php2shell-sapi-post":         ("mechanism", (0, 0, 0), (0, 0, 0)),
    "php2shell-backtrace":         ("mechanism", (1, 1, 1), (1, 1, 1)),
    "php2shell-request-lifecycle": ("mechanism", (1, 0, 1), (4, 4, 0)),
    "php2shell-setcookie":         ("hardening", (1, 1, 1), (4, 4, 4)),
    "php2shell-memstream":         ("hardening", (1, 1, 1), (0, 4, 3)),
    "php2shell-var-serialize":     ("mechanism", (0, 1, 1), (0, 0, 1)),
    "php2shell-unserializer":      ("mechanism", (1, 1, 1), (2, 0, 2)),
    "php-fcgi-ipv6-acl":           ("named",     (1, 1, 1), (0, 0, 0)),
    "php-openssl-cn-fallback":     ("mechanism", (0, 0, 0), (0, 4, 0)),
    "php-openssl-wildcard-oob":    ("named",     (1, 0, 1), (1, 0, 0)),
    "php-http-redirect-creds":     ("mechanism", (1, 1, 1), (3, 4, 1)),
    "php-soap-xml-recursion":      ("named",     (1, 1, 1), (0, 0, 4)),
    "php-soap-http-overflow":      ("mechanism", (1, 1, 1), (4, 4, 1)),
    "php-phar-tar-overflow":       ("mechanism", (1, 1, 0), (4, 4, 0)),
    "php-filter-encode-0xff":      ("named",     (1, 1, 1), (0, 0, 0)),
    "php-mysqlnd-ps-overread":     ("mechanism", (0, 1, 1), (0, 0, 3)),
    "php-win-reserved-names":      ("mechanism", (0, 0, 0), (0, 1, 0)),
    "wordpress-locate-template":   ("named",     (0, 0, 0), (0, 0, 0)),
}
EXPECTED_ALL, EXPECTED_NONE = 10, 5
# token totals over all 176 calls (22 cases x 4 passes x pre/post):
# [input_tokens, cache_creation_input_tokens, cache_read_input_tokens, output_tokens]
EXPECTED_TOKENS = {
    "Opus 5.5":   [704, 937860, 2988652, 155344],
    "Sonnet 5.5": [704, 937860, 2988652, 93447],
    "Haiku 5.5":  [704, 937860, 2988652, 233945],
}
# gemma (warning only): [cases, pass@4 hit, single-pass recall, post FPR,
# post any-flag, cases_truncated (post-cutoff), truncated calls /176, non-JSON replies /176]
EXPECTED_GEMMA = [20, 0.10, 0.03, 0.10, 0.20, 12, 96, 84]

TOL = 0.01
drift: list[str] = []
warn: list[str] = []


def r2(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(x) -> str:
    return str(x) if isinstance(x, int) else str(r2(x))


def cmp(label: str, got, exp, sink: list[str] | None = None) -> None:
    sink = drift if sink is None else sink
    if exp is None:
        return
    if isinstance(exp, int) and not isinstance(exp, bool) and isinstance(got, int):
        if got != exp:
            sink.append(f"{label}: got {got}, expected {exp}")
        return
    if abs(r2(got) - Decimal(str(exp))) > Decimal(str(TOL)):
        sink.append(f"{label}: got {r2(got)}, expected {exp}")


def load_case_ids() -> set[str]:
    ids = set()
    for line in CASES.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            ids.add(json.loads(line)["id"])
    return ids


def load(name: str) -> dict:
    path = RESULTS / name
    if not path.exists():
        print(f"FAIL: missing results file {path.name}")
        sys.exit(1)
    return json.loads(path.read_text())


def no_json(r: dict) -> bool:
    return not r.get("parsed", False)


def main() -> int:
    case_ids = load_case_ids()
    data = {m: load(f) for m, f in FILES.items()}
    gemma = load(GEMMA[1])

    # kill clause (b): runs and case set must agree
    for m, d in list(data.items()) + [(GEMMA[0], gemma)]:
        if d.get("n_cases") != 22:
            print(f"FAIL (b): {m} n_cases={d.get('n_cases')}, expected 22")
            return 1
        extra = {r["case"] for r in d["records"]} - case_ids
        if extra:
            print(f"FAIL (b): {m} has record case ids not in cases.jsonl: {sorted(extra)}")
            return 1
    print(f"case set: {len(case_ids)} ids in cases.jsonl; all four results files n_cases=22, record ids subset: ok")
    print("rounding: two decimals, half-up (decimal.ROUND_HALF_UP on the stored value)\n")

    for split, title in (("cutoff=post", "post-cutoff cases"),
                         ("tier=named", "tier=named (all 22 cases: 6 post-cutoff + 2 pre-cutoff)"),
                         ("tier=mechanism", "tier=mechanism (all 12 are post-cutoff)")):
        print(f"== {title}  [summary.aggregate['{split}']]")
        print("| model | " + " | ".join(h for h, _ in COLS) + " |")
        for m in CLAUDE:
            agg = data[m]["summary"]["aggregate"][split]
            cells = [agg[k] for _, k in COLS]
            print(f"| {m} | " + " | ".join(fmt(c) for c in cells) + " |")
            for (h, _), got, exp in zip(COLS, cells, EXPECTED[split][m]):
                cmp(f"{split} / {m} / {h}", got, exp)
        print()

    # reply health on post-cutoff cases
    print("== reply health, post-cutoff cases (records)")
    print(f"| model | post-patch calls | no JSON | hit max_tokens={MAX_TOKENS} | pre-patch no JSON | pre hit max_tokens | post any-flag among parsed |")
    for m in CLAUDE:
        d = data[m]
        post_ids = {k for k, v in d["summary"]["per_case"].items() if v["cutoff"] == "post"}
        recs = [r for r in d["records"] if r["case"] in post_ids and "error" not in r]
        post = [r for r in recs if r["variant"] == "post"]
        pre = [r for r in recs if r["variant"] == "pre"]
        nj = [r for r in post if no_json(r)]
        cap = sum(1 for r in nj if (r.get("usage") or {}).get("output_tokens") == MAX_TOKENS)
        parsed = [r for r in post if not no_json(r)]
        flag_parsed = sum(bool(r["predicted"]) for r in parsed) / len(parsed)
        pre_njl = [r for r in pre if no_json(r)]
        pre_cap = sum(1 for r in pre_njl if (r.get("usage") or {}).get("output_tokens") == MAX_TOKENS)
        row = [len(post), len(nj), cap, len(pre_njl), pre_cap, flag_parsed]
        print(f"| {m} | " + " | ".join(fmt(c) for c in row) + " |")
        for h, got, exp in zip(("post calls", "no JSON", "max_tokens", "pre no JSON", "pre max_tokens", "any-flag|parsed"),
                               row, EXPECTED_HEALTH[m]):
            cmp(f"health / {m} / {h}", got, exp)
    print()

    # case-level agreement
    print("== case-level agreement, post-cutoff (summary.per_case)")
    print("| case | tier | Opus | Sonnet | Haiku | post flagged-fixed /4 (O/S/H) |")
    pcs = {m: data[m]["summary"]["per_case"] for m in CLAUDE}
    post_cases = [c for c, v in pcs["Opus 5.5"].items() if v["cutoff"] == "post"]
    n_all = n_none = 0
    none_list = []
    for c in post_cases:
        hits = tuple(int(bool(pcs[m][c]["hit_any_pass"])) for m in CLAUDE)
        ff = tuple(int(pcs[m][c]["post_flagged_fixed_passes"]) for m in CLAUDE)
        tier = pcs["Opus 5.5"][c]["tier"]
        print(f"| {c} | {tier} | " + " | ".join("hit" if h else "miss" for h in hits)
              + " | " + "/".join(map(str, ff)) + " |")
        n_all += all(hits)
        if not any(hits):
            n_none += 1
            none_list.append(c)
        exp = EXPECTED_CASES.get(c)
        if exp is None:
            drift.append(f"case {c}: not in expected case table")
        elif exp != (tier, hits, ff):
            drift.append(f"case {c}: got {(tier, hits, ff)}, expected {exp}")
    missing = set(EXPECTED_CASES) - set(post_cases)
    if missing:
        drift.append(f"case table: expected cases absent from results: {sorted(missing)}")
    print(f"\nfound by all three: {n_all} of {len(post_cases)}")
    print(f"found by none: {n_none} of {len(post_cases)} ({', '.join(none_list)})\n")
    cmp("found by all three", n_all, EXPECTED_ALL)
    cmp("found by none", n_none, EXPECTED_NONE)

    # tokens
    print("== token totals, all 176 calls per model (records[*].usage)")
    print("| model | input (uncached) | cache write | cache read | input total | output |")
    for m in CLAUDE:
        tot = [0, 0, 0, 0]
        for r in data[m]["records"]:
            u = r.get("usage") or {}
            for i, k in enumerate(("input_tokens", "cache_creation_input_tokens",
                                   "cache_read_input_tokens", "output_tokens")):
                tot[i] += int(u.get(k) or 0)
        inp = tot[0] + tot[1] + tot[2]
        print(f"| {m} | {tot[0]:,} | {tot[1]:,} | {tot[2]:,} | {inp:,} | {tot[3]:,} |")
        exp = EXPECTED_TOKENS[m]
        if exp is not None:
            for h, got, e in zip(("input", "cache write", "cache read", "output"), tot, exp):
                cmp(f"tokens / {m} / {h}", got, e)
    print()

    # gemma: context only, not comparable
    agg = gemma["summary"]["aggregate"]["cutoff=post"]
    recs = gemma["records"]
    trunc_calls = sum(1 for r in recs if r.get("truncated"))
    nj = sum(no_json(r) for r in recs)
    row = [agg["cases"], agg["pass_at_k_case_hit_rate"], agg["mean_single_pass_recall"],
           agg["post_fpr_fixed_fn"], agg["post_any_flag_rate"], agg["cases_truncated"], trunc_calls, nj]
    print("== gemma4-e4b-ctx16k, post-cutoff: NOT COMPARABLE (format floor)")
    print("| cases | pass@4 hit | single-pass recall | post FPR | post any-flag | cases_truncated | truncated calls /176 | non-JSON replies /176 |")
    print("| " + " | ".join(fmt(c) for c in row) + " |\n")
    for h, got, e in zip(("cases", "pass@4", "single-pass", "FPR", "any-flag", "cases_truncated",
                          "truncated calls", "non-JSON"), row, EXPECTED_GEMMA):
        cmp(f"gemma / {h}", got, e, sink=warn)

    for w in warn:
        print(f"WARN (gemma, not comparable, does not fail): {w}")
    if drift:
        for d_ in drift:
            print(f"DRIFT: {d_}")
        print(f"\nFAIL: {len(drift)} cell(s) drift from findings.md")
        return 1
    print("OK: every posted cell re-derives from the results files (tolerance 0.01)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
