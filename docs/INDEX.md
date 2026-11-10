# Investigations index

One line per investigation with its headline result. Planned entries have no
directory yet, on purpose: an investigation gets a directory only when it has a
question and is about to be run.

| # | investigation | status | headline |
|---|---|---|---|
| 01 | CVE localization | closed (chapter 0, see notes/php-ai-auditor.md) | 22 cases, 20 post-cutoff (PHP2Shell + Sept 2026 php-src + WordPress). Opus 5.5, 4 passes: single-pass recall 0.21, union 0.43, **post-patch FPR 0.30**, flags something on 84% of clean files. Named-function cases 0.47 / FPR 0.13; mechanism cases 0.09 / FPR 0.40. Local gemma4-e4b: recall 0.03 with half the replies non-JSON (format floor, not comparable); qwen3/llama3.1 runs stopped by host memory pressure, to rerun. |
| 02 | Memory poisoning | case set frozen 2026-11-08, not run (private case set; run: lane lab-asl-09) | a planted lesson in the sandbox's harness-managed lesson library, read side (02a) and write side (02b), canary pairs, reported as consequence, persistence, concealment and repair (`docs/QUESTIONS.md`) |
| 03 | Secret hygiene in logs | run (private results) | read-only fingerprint scan of local agent state and MCP configs; cross-references secrets that also appear in transcripts/memory (private results) |
| 04 | Dependency exposure | run 2026-10-23 (private results) | names in manifests and in agents' recorded install commands checked for registry existence, published slopsquat list, edit-distance-1 to top PyPI packages (private results) |
| 05 | Model comparison | closed (chapter 0, see notes/php-ai-auditor.md) | on 20 post-cutoff cases Haiku 5.5 ≥ Opus 5.5 ≈ Sonnet 5.5 on recall (0.34 / 0.21 / 0.33 single-pass); Sonnet flags fixed functions 43% of the time; Haiku's apparent 51% any-flag rate is mostly capped non-answers (0.79 among parsed replies); 5 cases missed by all three; re-derive with `investigations/05-model-comparison/check.py` |
| 06 | Defenses and their cost | planned (run: lane lab-asl-11) | arms none / confirm-on-mutate / redaction / spotlighting / prompt hardening against a fixed list of rewrite classes; ASR, utility loss and call overhead reported together (`docs/QUESTIONS.md`) |
| 07 | Indirect injection, hosted vs local | run 2026-11-06 (counts public, cases private) | the sandbox's seven planted-instruction cases, two creator-pinned hosted models beside the local 2B champion's snapshot, graded on the injection-specific checks only: hosted 7/7 and 7/7, local 2B 4/7; 0 cases fool every column, 0 mutating tool calls (`investigations/07-injection-hosted/receipt.json`) |
| 08 | Confirm-on-mutate | run 2026-11-06 (counts public, cases private) | a code-only rule that holds a CRM write whose arguments come from tool results and not from the user's request, replayed over recorded hosted/local trajectories and constructed injection variants: the pre-registered rule holds 3 of 5 planted writes verbatim and 9 of 15 across spellings, with 0 of 25 recorded and 0 of 4 constructed false stops; the widest arm 4 of 5 and 12 of 15 (`investigations/08-confirm-on-mutate/receipt.json`) |
| 08b | Confirm-on-mutate on ten legitimate writes | run 2026-11-08 (private results); kill fired, no false-stop table | ten lab-authored CRM write cases (loosely named company, derived value, paraphrased value, plain), recorded on the two 07 hosted models and replayed through arms none / A / C and the pre-registered token-boundary arm D; the kill (a model failing the exam's own checks on a clean run) fired, so the private findings post which cases failed and why (private results) |
| 09 | PII redaction before the model | run 2026-11-07 (counts public, cases private) | a deterministic redactor (regex plus name lists) on the reply-draft exam inputs: recall on planted PII 53 of 63 exact-span (emails 11 of 11, tax ids 13 of 13, phones 15 of 16, names 14 of 23); the exam grader passes 24 of 25 before and after redaction in all three sits; 24 of 25 redacted replies echo a placeholder (`investigations/09-pii-redaction/receipt.json`) |
| 13 | Injection on mid-size local models | run 2026-11-10 (counts public, cases private) | 07's seven planted-instruction cases, same prompts and injection-only checks, on `gemma4:e4b` and `llama3.1:latest` (8B), three fresh-load passes each with identical verdicts. On 07's own count: e4b 4/7, Llama 5/7, the 2B 4/7, hosted 7/7 · 7/7. Counting valid cases only (the rule registered before the run): e4b 1/4 (its three CRM answers break the output protocol), Llama 4/6 (one refusal). Neither local tag resists more than one of the four same-channel cases (e4b 1/4, Llama 1/3 valid); 0 mutating tool calls (`investigations/13-local-tiers-injection/receipt.json`) |
| 10 | Tool-description poisoning | later | a poisoned tool schema as a third surface beside tool results and memory; not before 02 and 06 have posted (`docs/QUESTIONS.md`) |

## Notes

- `notes/php-ai-auditor.md`: chapter 0 (01 and 05), canonical: what was measured, the headline cells, the reopen threshold, and the PHP2Shell claims-vs-evidence record.
- `notes/2026-10-23-php2shell-claims-vs-evidence.md`: superseded by `notes/php-ai-auditor.md`; kept as the dated original.

## Public / private rule

Investigations 01 and 05 are public with their results: their targets are open models or
published CVEs. 02 and 06 publish their question, method and counts; their case files carry plant text and stay
private, as 07–09's do. Investigations 03 and 04 measure the author's own systems, so
their *results* live in a separate private repo; only their method may be
described here. 07–09 grade on the author's sandbox exams: their counts are public in each investigation's `receipt.json`, derived by
code from the private results, and `lab check` re-derives the INDEX and LESSONS rows from it; their case files, inputs,
trajectories, results and findings carry plant text and stay private (operator decision 9 Nov 2026). See the top-level
`README.md`.
