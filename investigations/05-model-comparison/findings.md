# Findings: model comparison

Re-derive: `python3 -I check.py` (stdlib only, no key, no GPU; reads the four
results files, prints every table below, exits 1 if any posted cell drifts by
more than 0.01; two decimals, half-up).

**Status:** frontier tier run 2026-10-23 (three models, 176 calls each);
one local model finished, two did not (see below). Raw data:
`../01-cve-localization/results/*.json`.

## Post-cutoff cases (n = 20), four passes, effort low

| model | pass@4 hit | single-pass recall | union recall | post FPR (fixed fn) | post any-flag | cand/call | input tokens | output tokens |
|---|---|---|---|---|---|---|---|---|
| Opus 5.5 | 0.65 | 0.21 | 0.43 | 0.30 | 0.84 | 0.74 | 3,927,216 | 155,344 |
| Sonnet 5.5 | 0.65 | 0.33 | 0.43 | **0.43** | **0.94** | 1.09 | 3,927,216 | 93,447 |
| Haiku 5.5 | **0.70** | **0.34** | **0.45** | 0.29 | **0.51**\* | 0.91 | 3,927,216 | 233,945 |

Tokens are totals over all 176 calls per model (22 cases, both variants),
from `records[*].usage`. Input = uncached 704 + cache write 937,860 + cache
read 2,988,652, identical across the three models. Cost ≈ at 23 Oct list prices:
Opus ≈ $9, Sonnet ≈ $4, Haiku ≈ $0.30.

\* Haiku's 0.51 counts 28 of 80 post-patch replies that hit the 2048
`max_tokens` cap with no JSON as "flagged nothing". Among the replies that
parsed, Haiku's post any-flag rate is 0.79 (Opus 0.85, Sonnet 0.94). See
Caveats.

By ground-truth tier (`summary.aggregate`, computed over all 22 cases, not
only post-cutoff: named = 6 post-cutoff + 2 pre-cutoff; mechanism = 12
post-cutoff; the 2 hardening cases are not shown):

| model | split | pass@4 hit | single-pass | union | post FPR | any-flag |
|---|---|---|---|---|---|---|
| Opus 5.5 | named (8) | 0.75 | 0.47 | 0.66 | 0.13 | 0.75 |
| Sonnet 5.5 | named | 0.63 | 0.44 | 0.56 | 0.09 | 0.84 |
| Haiku 5.5 | named | 0.63 | 0.44 | 0.53 | 0.16 | 0.50 |
| Opus 5.5 | mechanism (12) | 0.58 | 0.09 | 0.31 | 0.40 | 0.85 |
| Sonnet 5.5 | mechanism | 0.67 | 0.25 | 0.38 | 0.50 | 0.94 |
| Haiku 5.5 | mechanism | 0.67 | 0.19 | 0.35 | 0.25 | 0.50 |

## Case-level agreement (post-cutoff)

| case | tier | Opus | Sonnet | Haiku | post flagged-fixed /4 (O/S/H) |
|---|---|---|---|---|---|
| php2shell-session-rfc1867 | mechanism | hit | hit | hit | 1/2/3 |
| php2shell-opcache-persist | named | miss | miss | miss | 0/2/0 |
| php2shell-sapi-post | mechanism | miss | miss | miss | 0/0/0 |
| php2shell-backtrace | mechanism | hit | hit | hit | 1/1/1 |
| php2shell-request-lifecycle | mechanism | hit | miss | hit | 4/4/0 |
| php2shell-setcookie | hardening | hit | hit | hit | 4/4/4 |
| php2shell-memstream | hardening | hit | hit | hit | 0/4/3 |
| php2shell-var-serialize | mechanism | miss | hit | hit | 0/0/1 |
| php2shell-unserializer | mechanism | hit | hit | hit | 2/0/2 |
| php-fcgi-ipv6-acl | named | hit | hit | hit | 0/0/0 |
| php-openssl-cn-fallback | mechanism | miss | miss | miss | 0/4/0 |
| php-openssl-wildcard-oob | named | hit | miss | hit | 1/0/0 |
| php-http-redirect-creds | mechanism | hit | hit | hit | 3/4/1 |
| php-soap-xml-recursion | named | hit | hit | hit | 0/0/4 |
| php-soap-http-overflow | mechanism | hit | hit | hit | 4/4/1 |
| php-phar-tar-overflow | mechanism | hit | hit | miss | 4/4/0 |
| php-filter-encode-0xff | named | hit | hit | hit | 0/0/0 |
| php-mysqlnd-ps-overread | mechanism | miss | hit | hit | 0/0/3 |
| php-win-reserved-names | mechanism | miss | miss | miss | 0/1/0 |
| wordpress-locate-template | named | miss | miss | miss | 0/0/0 |

Found by all three: 10 of 20. Found by none: 5 of 20 (opcache persist,
SAPI post handler, OpenSSL CN fallback, Windows reserved names, WordPress
locate_template).

## Reading

1. **Tier does not predict recall here.** Haiku 5.5 matches or edges Opus
   5.5 on every recall metric at roughly one thirtieth of the cost. The
   spread across the three models (0.21 to 0.34 single-pass) is within what
   four passes on 20 cases can resolve; no model is separable from the
   others on recall. Haiku's recall is a lower bound: 14 of its 80
   pre-patch replies hit the output cap with no JSON and score as misses.
2. **Tier does change specificity, in the wrong direction for Sonnet.**
   Sonnet 5.5 flags a fixed function in 43% of clean-file calls and flags
   something in 94%. Haiku flags something in only 51%. Opus sits between.
   The model that says "none" most often is the cheapest one.
   *Correction (2026-11-06, from `check.py`):* that last sentence does not
   hold. Haiku's low any-flag rate is mostly non-answers: 28 of its 80
   post-patch replies hit the 2048-token cap with no JSON. Among replies
   that parsed, Haiku flags something in 79% of clean-file calls (Opus 85%,
   Sonnet 94%). The Sonnet result stands.
3. **The misses are shared.** Five cases defeat all three models, including
   the two PHP2Shell files whose functions the write-ups name
   (`zend_accel_script_persist`, `sapi_handle_post`) and the WordPress fix.
   These are the cases where the vulnerability is a cross-request state
   property or a path-policy property, not a local pattern in the function
   body. Whole-file context did not rescue them.
4. **The same functions trip every model on the fixed file.**
   `php_setcookie` is flagged 4/4 by all three on the patched file;
   `make_http_soap_request` and `phar_parse_tarfile` 4/4 by two of three.
   These are functions that *look* dangerous in both versions. A reviewer
   using any of these models as a filter would re-triage them after every
   patch.
5. **Implication for the "AI found PHP2Shell" narrative.** Given the exact
   file and asked the plain question, none of the three frontier tiers
   reliably points at the opcache or SAPI functions that the human-led,
   AI-assisted audits found. The discovery took a human hunch, exploit
   iteration and weeks; this harness measures the zero-shot floor, and that
   floor is low and flat across tiers.

## Local models

One of three finished. `gemma4-e4b-ctx16k` (176 calls, files truncated at
40k characters): pass@4 hit rate 0.10, single-pass recall 0.03, post-patch
FPR 0.10, flags anything on 20% of clean files. 96 of 176 calls saw a
truncated file and only 92 of 176 replies contained a JSON object; 76 of 88
pre-patch replies named no function. That is a format-compliance floor, not
a specificity result, and the row is not comparable to the frontier table.
`qwen3-8b-ctx24k` was stopped by the host after 16 calls (memory pressure)
and `llama31-ctx16k` did not start; both are to be rerun on their own.

## Caveats

Same as investigation 01: effort `low`, no sampling control, file path in
the prompt, commit-derived ground truth with a hand filter, n = 20 and four
passes, so differences under about 0.1 are noise.

Reply health on the post-cutoff cases (printed by `check.py`): replies with no
JSON, out of 80 post-patch / 80 pre-patch calls, are Opus 1 / 5, Sonnet 0 / 0,
Haiku 28 / 14. Every one of these hit `max_tokens` = 2048 (`lab/models.py`) and
scores as an empty answer. That pushes Haiku's recall, FPR and any-flag down.
The tier rows are over all 22 cases (see the note above that table).

## Registration

This comparison was not pre-registered. `question.md` was written at
21:06 UTC (22:06 local) on 23 Oct. That is after all three frontier runs had
finished: their results files are stamped at the end of each run, at 20:27,
20:49 and 21:05 UTC. The only thing registered before this posting lane ran
was its kill clause: no posting if any post-cutoff cell failed to re-derive
within 0.01, or if a results file disagreed with the case set.

## Refused

No reruns. No local-model rows beyond gemma's format-floor line:
`qwen3-8b-ctx24k` and `llama31-ctx16k` were stopped by host memory pressure on
23 Oct, and rerunning them is GPU work, outside this lane. No new cases.

## Reopen threshold

This reopens if either of these appears: a post-cutoff batch of ≥ 10 new CVEs
with one-file fixes, or a local model with ≥ 64k context that fits in 16 GB.
Either one reopens the comparison under a pre-registered prediction.
