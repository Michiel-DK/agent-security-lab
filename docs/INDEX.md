# Investigations index

One line per investigation with its headline result. Planned entries have no
directory yet, on purpose: an investigation gets a directory only when it has a
question and is about to be run.

| # | investigation | status | headline |
|---|---|---|---|
| 01 | CVE localization | closed (chapter 0, see notes/php-ai-auditor.md) | 22 cases, 20 post-cutoff (PHP2Shell + Sept 2026 php-src + WordPress). Opus 5.5, 4 passes: single-pass recall 0.21, union 0.43, **post-patch FPR 0.30**, flags something on 84% of clean files. Named-function cases 0.47 / FPR 0.13; mechanism cases 0.09 / FPR 0.40. Local gemma4-e4b: recall 0.03 with half the replies non-JSON (format floor, not comparable); qwen3/llama3.1 runs stopped by host memory pressure, to rerun. |
| 02 | Memory poisoning | planned (case set: lane lab-asl-07; run: lane lab-asl-09) | a planted lesson in the sandbox's harness-managed lesson library, read side (02a) and write side (02b), canary pairs, reported as consequence, persistence, concealment and repair (`docs/QUESTIONS.md`) |
| 03 | Secret hygiene in logs | run (private results) | read-only fingerprint scan of local agent state and MCP configs; cross-references secrets that also appear in transcripts/memory (private results) |
| 04 | Dependency exposure | run (2026-10-23) | names in manifests and in agents' recorded install commands checked for registry existence, published slopsquat list, edit-distance-1 to top PyPI packages (private results) |
| 05 | Model comparison | closed (chapter 0, see notes/php-ai-auditor.md) | on 20 post-cutoff cases Haiku 5.5 ≥ Opus 5.5 ≈ Sonnet 5.5 on recall (0.34 / 0.21 / 0.33 single-pass); Sonnet flags fixed functions 43% of the time; Haiku's apparent 51% any-flag rate is mostly capped non-answers (0.79 among parsed replies); 5 cases missed by all three; re-derive with `investigations/05-model-comparison/check.py` |
| 06 | Defenses and their cost | planned (run: lane lab-asl-11) | arms none / confirm-on-mutate / redaction / spotlighting / prompt hardening against a fixed list of rewrite classes; ASR, utility loss and call overhead reported together (`docs/QUESTIONS.md`) |
| 07 | Indirect injection, hosted vs local | run 2026-11-06 (private results) | the sandbox's seven planted-instruction cases, two creator-pinned hosted models beside the local 2B champion's snapshot, graded on the injection-specific checks only (private results) |
| 08 | Confirm-on-mutate | run 2026-11-06 (private results) | a code-only rule that holds a CRM write whose arguments come from tool results and not from the user's request, replayed over recorded hosted/local trajectories and constructed injection variants; catches and false stops posted as counts in the private findings (private results) |
| 09 | PII redaction before the model | run 2026-11-07 (private results) | a deterministic redactor (regex plus name lists) on the reply-draft exam inputs: recall on planted names, tax ids, emails and phones against a key frozen before the redactor, and the exam grader's pass counts before and after redaction on the original inputs; both posted as counts in the private findings (private results) |
| 10 | Tool-description poisoning | later | a poisoned tool schema as a third surface beside tool results and memory; not before 02 and 06 have posted (`docs/QUESTIONS.md`) |

## Notes

- `notes/php-ai-auditor.md`: chapter 0 (01 and 05), canonical: what was measured, the headline cells, the reopen threshold, and the PHP2Shell claims-vs-evidence record.
- `notes/2026-10-23-php2shell-claims-vs-evidence.md`: superseded by `notes/php-ai-auditor.md`; kept as the dated original.

## Public / private rule

Investigations 01, 02, 05, 06 are public: their targets are open models or
published CVEs. Investigations 03 and 04 measure the author's own systems, so
their *results* live in a separate private repo; only their method may be
described here. 07–09 grade on the author's sandbox exams; each lane decides,
before it posts, whether its cases can be public. 07–09 cases carry plant text and stay private unless the operator
says otherwise. See the top-level `README.md`.
