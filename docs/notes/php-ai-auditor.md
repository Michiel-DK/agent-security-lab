# Chapter 0: AI as auditor on the October 2026 PHP disclosures

> STATUS: canonical for chapter 0 (investigations 01 and 05). Closed 2026-11-08. Supersedes
> `notes/2026-10-23-php2shell-claims-vs-evidence.md`, whose content is folded in below.
> Every lab number on this page ("Headline cells", "What it says") is copied from
> `investigations/01-cve-localization/findings.md`, `investigations/05-model-comparison/findings.md` or the 01 row of
> `docs/INDEX.md`. `python3 -m lab check 01` and `python3 -m lab check 05` re-derive those files from the committed
> results. For any figure not shown here, see the findings files. The PHP2Shell section at the end is a dated record of
> outward claims as of 23 October 2026, with its sources listed. Its figures are not lab results, and no check covers them.

## Why this chapter existed

The PHP disclosures of October 2026 (PHP2Shell, CVE-2026-109618 and CVE-2026-109619) were reported as "found with AI".
The public reaction assumed that models can reliably point at vulnerabilities. Chapter 0 measured the zero-shot floor
under that claim. A model gets one whole source file that is known to be vulnerable and has to name the function the
official fix changed. It then gets the fixed file, where it should stop flagging that function.

## What was measured

- **01, CVE localization.** 22 public CVE cases, each with an official fix commit in one file. 20 are post-cutoff
  (PHP2Shell, Sept 2026 php-src, WordPress) and 2 are a pre-cutoff contamination control. Each case runs four passes
  on the pre-patch file and four on the post-patch file. Scoring is by exact function name against commit-derived
  ground truth. There is no judge.
- **05, model comparison.** The same harness and cases, rerun across three frontier tiers, plus one local model that
  only reached a format floor.

## Headline cells

01, Opus 5.5, from the INDEX 01 row (re-derived by `lab check 01`):

> 22 cases, 20 post-cutoff (PHP2Shell + Sept 2026 php-src + WordPress). Opus 5.5, 4 passes: single-pass recall 0.21,
> union 0.43, **post-patch FPR 0.30**, flags something on 84% of clean files. Named-function cases 0.47 / FPR 0.13;
> mechanism cases 0.09 / FPR 0.40. Local gemma4-e4b: recall 0.03 with half the replies non-JSON (format floor, not
> comparable)

05, post-cutoff cases (n = 20), four passes, effort low (table copied from 05's findings; re-derived by `lab check 05`):

| model | pass@4 hit | single-pass recall | union recall | post FPR (fixed fn) | post any-flag | cand/call |
|---|---|---|---|---|---|---|
| Opus 5.5 | 0.65 | 0.21 | 0.43 | 0.30 | 0.84 | 0.74 |
| Sonnet 5.5 | 0.65 | 0.33 | 0.43 | **0.43** | **0.94** | 1.09 |
| Haiku 5.5 | **0.70** | **0.34** | **0.45** | 0.29 | **0.51**\* | 0.91 |

\* Haiku's 0.51 counts 28 of 80 post-patch replies that hit the 2048 `max_tokens` cap with no JSON as "flagged
nothing". Among the replies that parsed, Haiku's post any-flag rate is 0.79 (Opus 0.85, Sonnet 0.94).

Found by all three: 10 of 20. Found by none: 5 of 20 (opcache persist, SAPI post handler, OpenSSL CN fallback, Windows
reserved names, WordPress locate_template).

## What it says

The longer readings are in the two findings files. In short:

1. Recall is low, and model tier does not change it. The three tiers cannot be separated on recall at n = 20 with four
   passes.
2. Specificity is the weak side. The models flag risky-looking functions on the already-fixed file as well. They are
   not recognising the bug.
3. The two PHP2Shell files whose functions the write-ups name (opcache persist, SAPI post handler) were missed by all
   three tiers. The discovery took a human hunch, iteration and weeks. This harness measured the zero-shot floor, and
   that floor is low and flat across tiers.
4. Caveats (from the findings): effort `low`, no sampling control, the file path is in the prompt, ground truth is
   commit-derived with a hand filter, and 05 was not pre-registered (05's findings, "Registration").

## Reopen threshold (from 05)

This reopens if either of these appears: a post-cutoff batch of ≥ 10 new CVEs with one-file fixes, or a local model
with ≥ 64k context that fits in 16 GB. Either one reopens the comparison under a pre-registered prediction. Until then,
01 and 05 are not rerun, and their directories stay so that `lab check` keeps re-deriving them.

## The claims behind the question: PHP2Shell, 21 to 23 October 2026

Folded in from `notes/2026-10-23-php2shell-claims-vs-evidence.md`, unchanged in substance. It is a dated record of what
was said about CVE-2026-109618 and CVE-2026-109619 in the first 72 hours, next to what was measurable. It contains no
exploit detail. Status is as of 23 October 2026.

### Day 0 claims (21 October)

| claim | source | status on 23 October |
|---|---|---|
| "Could take down 70% of the internet" | Fortune, Wiz framing | 70% is PHP's share of websites (W3Techs). No measure of exploitable share exists. VulnCheck: ~2.6M internet-facing PHP hosts; 700k+ on unpatchable 3.x to 7.3. Banner counts, not vulnerability. |
| Comparable to Heartbleed | Wiz | Heartbleed had a universal single-request exploit. Sansec (22 Oct): no universal request exists for PHP2Shell; public PoCs fail on default PHP and most need an app-level LFI. |
| "Broadly exploited in the wild" | AWS statement, press | Attempts: yes, millions (Cloudflare CEO on X). Confirmed compromises: zero reported by any vendor as of 23 Oct (SecurityWeek roundup; Hunt.io 0/123 targets; SOCRadar 0/11; Wordfence none; Sophos retracted its one "successful exploit" report). |
| "Found with AI" | most headlines | AI-assisted, human-led. Calif: human hunch about 2024 OOM bug, GPT-5.6 Sol as helper, humans verified and coordinated. Wiz: one researcher, one week, Gemini 4 Argon + GPT-5.6 Sol + Wiz Atlas. php-src advisories credit four humans and no model. |
| CVSS 10 | watchTowr | PHP: 9.2 (CVSS 4.0). NVD 3.x: 9.8 and 8.1. |
| "PHP2Shell is leaking API keys from ecommerce servers" | ecomcrew headline | Risk description of the memory-disclosure path (freed worker memory in a PHPSESSID cookie). No incident of key theft reported. |
| Exploitation began after disclosure | early coverage | Amazon MadPot saw the first attempt on 17 Oct, four days before, after a PoC video leak and early Chainguard builds. CISA on 21 Oct: no exploitation observed. |

### What held up

- The bugs are real, in the engine, and reach every release since 5.4. Four
  bugs under two CVEs; a fifth related issue (CVE-2026-115560) was published
  as an informational advisory on 23 Oct with an ini mitigation.
- Patching is the only complete fix. 7.4 to 8.1 got source backports only;
  7.3 and older have nothing.
- Government response was real and large: Dutch, Finnish, French, Belgian,
  Czech and some Canadian sites went offline; UK NCSC, CERT-EU and US NSA
  advised taking unpatchable systems down.
- Attackers moved fast on volume: a Mirai-style botnet (payload "Potassium")
  added the CVEs within a day, and payloads mutated against WAF rules.

### What did not (yet)

- No confirmed compromise. No web shell counts. No skimmer campaign tied to
  it. No KEV listing as of 23 Oct morning.
- No universal exploit. Preconditions (SAPI, memory layout, app-level LFI,
  display_errors) matter; VulnCheck's ASLR-bypass is customers-only.

### Reading (23 October)

Within 48 hours the measured picture went from "Heartbleed for PHP" to "a
critical engine bug with a high bar to weaponise, patched before anyone is
known to have been hit". Both the 21 Oct severity framing and the 23 Oct
calm could be wrong by next week; this note records what each rested on.

### Claims vs the lab's evidence

The "found with AI" row is the one chapter 0 could test. The primary sources credit humans who used models as helpers.
01 and 05 measured the other side of that: given the exact file and the plain question, no frontier tier reliably named
the opcache or SAPI functions. The record agrees with the measurement. These were AI-assisted, human-led findings. The
lab's numbers do not support "a model finds this kind of bug on its own".

Primary sources: php-src GHSA-w8hw-w9fx-j79w and GHSA-6wmf-4rv5-p3rp; Wiz
research post; Cloudflare blog (WAF timeline); Sansec research page; CISA
alert 2026-10-21; watchTowr FAQ; SecurityWeek 2026-10-23; Daniel Stenberg
and Epoch AI for the wider "AI finds bugs" context. Fix commit: php-src
506e87fa7dcdd306975e5b8f8265ee03527aacbf (300 files, +11112 -1032).
