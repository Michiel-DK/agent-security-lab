# agent-security-lab

## Lab

A scripts-only lab that measures security techniques for agentic flows on the author's own sandbox exams. The exams
use fictional companies and contacts. Each investigation asks one question, with a small n. Its prediction is
committed before it runs, its case set and kill clause are written down first, and its grading is deterministic: no
model judge scores a number. Every posted number has a script that re-derives it from committed results, with no API
key, no model call and no GPU. The lab is scripts and results files only, with no notebook.

```sh
python3 -m lab check        # re-derives every posted number; exit 1 on drift
python3 -m lab check 01     # one investigation
```

In this public repo `lab check` re-derives 01 and 05. For 07, 08 and 09, whose results are private, it only asserts
that the INDEX rows carry no number. In the private source repo it re-derives all five.

**Chapter 0, AI as auditor (closed).** The lab started from the October 2026 PHP disclosures, which were reported as
"found with AI". Investigations 01 and 05 measured whether a model can name the vulnerable function in a known-vulnerable
file. They tested Opus 5.5 and then three model tiers on 20 post-cutoff CVEs. Recall was low and flat across tiers, and
models flagged already-fixed functions. The chapter is closed and has one canonical note,
`docs/notes/php-ai-auditor.md`, which carries the headline cells, the claims-vs-evidence record and the reopen
threshold.

A lab is read, not installed. The `lab` package exists to reproduce numbers, not to be a tool.

## Scope and ethics

- **Defensive only.** Investigations read code and measure behaviour. They do
  not produce exploits or payloads, and they do not attack systems.
- **Authorized targets only.** Public, published CVEs; open models; and the
  author's own systems. Nothing belonging to anyone else is probed.
- **No exploit recipes.** Write-ups describe the *class* of weakness and the
  measurement, never a working attack against a live system.

## Layout

```
lab/            shared harness: model clients, source fetcher, scoring; `python3 -m lab check|diff|run`
investigations/ one directory per run: question.md, run.py, dataset/, results/, findings.md
docs/INDEX.md   one line per investigation with its headline result
docs/QUESTIONS.md  the planned questions: case set, grader, kill clause
docs/CASES.md   which case set each investigation grades on
docs/notes/     dated notes; php-ai-auditor.md is canonical for chapter 0
```

## What is here vs. what is kept private

Some investigations measure the author's *own* agents, logs, and repos.
Publishing those results would map a real attack surface, so they are not here:
only the method is. This repo is published from a private working repo, and
investigations that touch the author's own systems keep their results there. A
local pre-commit leak guard blocks internal names and secret-shaped strings from
entering this repo; see `docs/INDEX.md` for which investigations are public.

This mirrors how security researchers publish: the technique and the benchmark
are public, a specific system's live findings are not.

## Running

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # only needed for the Claude backend
cp .env.example .env                        # then edit if using the API
python investigations/01-cve-localization/run.py
```

Defaults to a local Ollama model (`gemma4:e4b`), so no API key is required.
Set `MODEL_BACKEND=claude` with `ANTHROPIC_API_KEY` to compare against the API.

## Status

One line per investigation in `docs/INDEX.md`; planned questions in `docs/QUESTIONS.md`.

| | |
|---|---|
| closed (chapter 0) | 01 CVE localization · 05 model comparison. Both posted and re-derived by `lab check`; see `docs/notes/php-ai-auditor.md` |
| run, private results | 03 secret hygiene · 04 dependency exposure (they measure the author's own machine; 04 publishes only its `question.md`, 03 stays private in full because its question names local paths) |
| run, private results | 07 indirect injection, hosted vs local · 08 confirm-on-mutate · 09 PII redaction (sandbox exams; cases carry plant text) |
| planned | 02 memory poisoning (lanes lab-asl-07 case set, lab-asl-09 run) · 06 defenses and their cost (lane lab-asl-11) |
| later | 10 tool-description poisoning |

## License

MIT. See `LICENSE`.
