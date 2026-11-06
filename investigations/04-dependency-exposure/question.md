# Investigation 04: are hallucinated or squat-prone package names in my manifests or my agents' install commands?

## Question

LLMs invent package names at a measurable rate (4.6% to 6.1% across five
frontier models in a 2026 re-run of the USENIX Security 2025 study; 53 names
hallucinated identically by all five were still registrable in April 2026).
The published work measures the models. It does not measure a developer's
actual exposure: did any such name reach my dependency manifests, or did an
agent on my machine ever run an install command for a package that does not
exist?

## Design

- **Inputs, all local and the author's own:** dependency manifests under the
  author's code directory (`requirements*.txt`, `pyproject.toml`,
  `package.json`), and install commands recorded in agent session transcripts
  (`pip install`, `uv pip install`, `poetry add`, `npm install`, `pnpm add`,
  `yarn add`) found in `~/.claude/projects`, `~/.codex`, `~/.cursor`.
- **Checks, metadata only, nothing is installed:**
  1. Does the name exist on its registry (PyPI or npm JSON API)? A name that
     an agent tried to install and that does not exist is a hallucination an
     attacker could register.
  2. Is the name on the short list of publicly disclosed slopsquatting
     targets (Socket, April 2026: `css-color-stop`, `dns-sd`, `dom-ains`;
     the npm `unused-imports` case)?
  3. Is the name one edit away from a top-1000 package on its registry
     (typosquat-prone), when it is not itself in the top 1000?
- **Output:** counts, the list of nonexistent names with where they came
  from, and the near-miss list. Results are private (they describe the
  author's projects); the method is public.

## How to run

```
python3 -I run.py      # read-only; network access only to registry metadata endpoints
```
