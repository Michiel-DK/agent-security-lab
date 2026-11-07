# Investigation 05: does the model tier change the localization result?

## Question

Run investigation 01's harness, unchanged, across frontier API models and
small local models. Does a more capable (and more expensive) model find more
of the known vulnerable functions, and does it flag fewer already-fixed ones?

## Design

Identical to investigation 01: same 22 cases (20 post-cutoff), same prompt,
four passes, whole-file input. Only `MODEL_BACKEND` / `ANTHROPIC_MODEL` /
`OLLAMA_MODEL` change. Local models have 16k to 24k token contexts, so files
beyond `LAB_MAX_CHARS` are truncated and every truncated call is flagged in
the results; those numbers are reported separately and are not comparable to
the untruncated frontier runs.

Metrics as in 01: single-pass recall, union recall over four passes, case
pass@4 hit rate, post-patch false-positive rate on fixed functions, any-flag
rate on clean files, candidates per call. Cost per run is recorded from the
API usage fields.

## Why it matters

The capability story ("a better model finds more bugs") is what the public
reaction to AI-found CVEs assumes. IPI Arena found capability and injection
robustness only weakly correlated (r = -0.31, not significant); the May 2026
frontier evaluation found every tier with 10 to 50% false positives. This
investigation asks the same question for localization on code the models
cannot have memorised.

## How to run

```
for m in claude-opus-5-5 claude-sonnet-5-5 claude-haiku-5-5; do
  MODEL_BACKEND=claude ANTHROPIC_MODEL=$m LAB_PASSES=4 LAB_MAX_CHARS=400000 python3 ../01-cve-localization/run.py
done
MODEL_BACKEND=ollama OLLAMA_MODEL=gemma4-e4b-ctx16k LAB_PASSES=4 LAB_MAX_CHARS=40000 python3 ../01-cve-localization/run.py
```
Results land in `../01-cve-localization/results/`; this directory holds the
comparison.
