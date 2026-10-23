# Investigations index

One line per investigation with its headline result. Planned entries have no
directory yet, on purpose: an investigation gets a directory only when it has a
question and is about to be run.

| # | investigation | status | headline |
|---|---|---|---|
| 01 | CVE localization | run | `gemma4:e4b` zero-shot whole-file recall = 0.00 on 2 verified public CVEs; clean baseline floor |
| 02 | Indirect-injection resistance | planned | how reliably an agent treats retrieved/fetched text as data, not instructions |
| 03 | Secret hygiene in logs | planned | scan of one's own session / memory / CI logs for leaked credentials (private results) |
| 04 | Dependency exposure | planned | confusable / typosquat-prone names in one's own manifests (private results) |
| 05 | Model comparison | planned | investigation 01's harness run across local vs API models |
| 06 | Defenses and their cost | planned | risk reduction vs capability lost for the two worst findings above |

## Public / private rule

Investigations 02, 05, 06 are public: their targets are open models or
published CVEs. Investigations 03 and 04 measure the author's own systems, so
their *results* live in a separate private repo; only their method may be
described here. See the top-level `README.md`.
