# agent-security-lab

A lab notebook for AI-agent security. Each investigation asks one question,
runs a reproducible experiment, and records a measured result. The method and
the harness are the point, not any single number.

Built because the October 2026 PHP disclosures were found with AI and the public
reaction assumed models can reliably find vulnerabilities. Whether they can, and
how often they are wrong, is a measurable question. This repo measures it.

## Scope and ethics

- **Defensive only.** Investigations read code and measure behaviour. They do
  not produce exploits or payloads, and they do not attack systems.
- **Authorized targets only.** Public, published CVEs; open models; and the
  author's own systems. Nothing belonging to anyone else is probed.
- **No exploit recipes.** Write-ups describe the *class* of weakness and the
  measurement, never a working attack against a live system.

## Layout

```
lab/            shared harness: model clients, source fetcher, scoring
investigations/ one directory per run: question.md, run.py, dataset/, findings.md
docs/INDEX.md   one line per investigation with its headline result
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

See `docs/INDEX.md`. Investigation 01 is run with real numbers in its
`findings.md`; the rest are planned and intentionally have no directory yet.

## License

MIT. See `LICENSE`.
