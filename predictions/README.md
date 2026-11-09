# predictions/

`lab run` writes a new file under `investigations/<id>/results/` only after the run's prediction is committed here. One
file per run name. Run names, case sets and kill clauses for the planned questions are in `docs/QUESTIONS.md`
(`07-injection-hosted`, `08-confirm-on-mutate`, `09-pii-redaction`, `02-memory-poisoning`, `06-defense-cost`).

Required: two non-empty level-2 sections.

```markdown
# <run name>

## Prediction
What the number will do, against which baseline, on which metric. Say "unsure" if you are.

## Mechanism
Why. The argument that makes the prediction, written before the result exists.
```

The gate checks that the file is tracked by git and has no uncommitted edits, then records the commit in the results file.
