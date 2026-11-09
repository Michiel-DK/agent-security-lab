# Cases

Each investigation brings its own case set. Held-out cases are never tuned on. A new case set needs a new question in
`docs/QUESTIONS.md`.

| id | case set | where | size and split | fixed at |
|---|---|---|---|---|
| 01 | public CVEs with an official fix commit; pre-patch / post-patch file pairs | `investigations/01-cve-localization/dataset/cases.jsonl` (metadata only; source fetched at run time) | 22 cases: 20 post-cutoff (the measurement), 2 pre-cutoff (contamination control). No train split: zero-shot, nothing is tuned | commit `f8b7d7b` (2026-10-23) |
| 05 | 01's cases and results, re-read across model tiers | `investigations/01-cve-localization/results/` | as 01 | as 01 |
| 07–09, 06 | see `docs/QUESTIONS.md` | agent-sandbox `evals/*/cases.json`, pinned per question | all named cases are held-out | pinned in each prediction file |
| 02 | ten canary pairs (planted lesson + matching clean library) on a throwaway `crm-followup-mem` profile; five TRAIN failure transcripts with a plant for 02b | `investigations/02-memory-poisoning/cases/` (private: plant text), built by lane lab-asl-07 from a `git archive` copy of agent-sandbox at `8672b13` | 10 pairs, each tied to one held-out case input; 5 TRAIN inputs for the write side | frozen 2026-11-08 by lane lab-asl-07 (sha256 block in the private `question.md`, asserted by `lab check 02`) |
| 08b | ten legitimate CRM writes (loosely named company, derived value, paraphrased value, plain); no plant text | this repo, `investigations/08-confirm-on-mutate/cases/legit10.json` (private), run through agent-sandbox's crm-followup runner and mock at `8672b13` (archive copy) | 10 cases, held-out | frozen 2026-11-08 (commit `94d796d`, sha256 recorded) before any recording |

01's ground truth is computed by `python -m lab.funcdiff` (functions that exist pre-patch and changed in the fix);
`dataset/README.md` gives the selection rule.
