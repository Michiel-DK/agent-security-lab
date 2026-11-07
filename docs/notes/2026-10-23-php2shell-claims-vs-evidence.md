# PHP2Shell, 21 to 23 October 2026: claims versus evidence

A dated record of what was said about CVE-2026-109618 and CVE-2026-109619 in
the first 72 hours, next to what was measurable. This lab exists to record
exactly this kind of gap. No exploit detail is included.

## Day 0 claims (21 October)

| claim | source | status on 23 October |
|---|---|---|
| "Could take down 70% of the internet" | Fortune, Wiz framing | 70% is PHP's share of websites (W3Techs). No measure of exploitable share exists. VulnCheck: ~2.6M internet-facing PHP hosts; 700k+ on unpatchable 3.x to 7.3. Banner counts, not vulnerability. |
| Comparable to Heartbleed | Wiz | Heartbleed had a universal single-request exploit. Sansec (22 Oct): no universal request exists for PHP2Shell; public PoCs fail on default PHP and most need an app-level LFI. |
| "Broadly exploited in the wild" | AWS statement, press | Attempts: yes, millions (Cloudflare CEO on X). Confirmed compromises: zero reported by any vendor as of 23 Oct (SecurityWeek roundup; Hunt.io 0/123 targets; SOCRadar 0/11; Wordfence none; Sophos retracted its one "successful exploit" report). |
| "Found with AI" | most headlines | AI-assisted, human-led. Calif: human hunch about 2024 OOM bug, GPT-5.6 Sol as helper, humans verified and coordinated. Wiz: one researcher, one week, Gemini 4 Argon + GPT-5.6 Sol + Wiz Atlas. php-src advisories credit four humans and no model. |
| CVSS 10 | watchTowr | PHP: 9.2 (CVSS 4.0). NVD 3.x: 9.8 and 8.1. |
| "PHP2Shell is leaking API keys from ecommerce servers" | ecomcrew headline | Risk description of the memory-disclosure path (freed worker memory in a PHPSESSID cookie). No incident of key theft reported. |
| Exploitation began after disclosure | early coverage | Amazon MadPot saw the first attempt on 17 Oct, four days before, after a PoC video leak and early Chainguard builds. CISA on 21 Oct: no exploitation observed. |

## What held up

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

## What did not (yet)

- No confirmed compromise. No web shell counts. No skimmer campaign tied to
  it. No KEV listing as of 23 Oct morning.
- No universal exploit. Preconditions (SAPI, memory layout, app-level LFI,
  display_errors) matter; VulnCheck's ASLR-bypass is customers-only.

## Reading

Within 48 hours the measured picture went from "Heartbleed for PHP" to "a
critical engine bug with a high bar to weaponise, patched before anyone is
known to have been hit". Both the 21 Oct severity framing and the 23 Oct
calm could be wrong by next week; this note records what each rested on.

Primary sources: php-src GHSA-w8hw-w9fx-j79w and GHSA-6wmf-4rv5-p3rp; Wiz
research post; Cloudflare blog (WAF timeline); Sansec research page; CISA
alert 2026-10-21; watchTowr FAQ; SecurityWeek 2026-10-23; Daniel Stenberg
and Epoch AI for the wider "AI finds bugs" context. Fix commit: php-src
506e87fa7dcdd306975e5b8f8265ee03527aacbf (300 files, +11112 -1032).
