# Investigations index

One line per investigation with its headline result. Planned entries have no
directory yet, on purpose: an investigation gets a directory only when it has a
question and is about to be run.

| # | investigation | status | headline |
|---|---|---|---|
| 01 | CVE localization | run (2026-10-23) | 22 cases, 20 post-cutoff (PHP2Shell + Sept 2026 php-src + WordPress). Opus 5.5, 4 passes: single-pass recall 0.21, union 0.43, **post-patch FPR 0.30**, flags something on 84% of clean files. Named-function cases 0.47 / FPR 0.13; mechanism cases 0.09 / FPR 0.40. Local gemma4-e4b: recall 0.03 with half the replies non-JSON (format floor, not comparable); qwen3/llama3.1 runs stopped by host memory pressure, to rerun. |
| 02 | Indirect-injection resistance | redesign | being rewritten as memory poisoning of harness-managed agent memory (sandbox profile, canary goals); single-turn text tests are no longer the 2026 bar |
| 03 | Secret hygiene in logs | run (private results) | read-only fingerprint scan of local agent state and MCP configs; cross-references secrets that also appear in transcripts/memory (private results) |
| 04 | Dependency exposure | run (2026-10-23) | names in manifests and in agents' recorded install commands checked for registry existence, published slopsquat list, edit-distance-1 to top PyPI packages (private results) |
| 05 | Model comparison | run + posted 2026-11-06 (frontier; local gemma format floor only) | on 20 post-cutoff cases Haiku 5.5 ≥ Opus 5.5 ≈ Sonnet 5.5 on recall (0.34 / 0.21 / 0.33 single-pass); Sonnet flags fixed functions 43% of the time; Haiku's apparent 51% any-flag rate is mostly capped non-answers (0.79 among parsed replies); 5 cases missed by all three; re-derive with `investigations/05-model-comparison/check.py` |
| 06 | Defenses and their cost | planned | adaptive attacker on top of 02; report ASR, utility loss and call overhead together |

## Notes

- `notes/2026-10-23-php2shell-claims-vs-evidence.md`: what was claimed about PHP2Shell on 21 October versus what was measurable by 23 October.

## Public / private rule

Investigations 01, 02, 05, 06 are public: their targets are open models or
published CVEs. Investigations 03 and 04 measure the author's own systems, so
their *results* live in a separate private repo; only their method may be
described here. See the top-level `README.md`.
