# Tweet from 0xMarioNawfal — Cloudflare security-audit skill

Capture: `ReadItLater Inbox/Tweet from 0xMarioNawfal (2026-10-19 14-34-07).md`
Origin: <https://x.com/RoundtableSpace/status/2112125353594401162>
Verdict: **adopt**

## The origin as resolved

Read through the twitter skill (`twikit-cli tweet 2112125353594401162`), not a search. Posted 2026-10-19 by
0xMarioNawfal (@RoundtableSpace); 4034 likes, 377 retweets, 81 replies, about 345k views. The API returns the note
truncated: "Cloudflare open-sourced the security audit skill that seeded its own vulnerability hunting harness. Your
coding agent can now run it on your code. How it works, in 6 phases: maps your codebase, hunts for bugs area by area so
nothing gets skipped, sends every finding to a..." The tweet is a pointer; the thing itself is the repository it names,
<https://github.com/cloudflare/security-audit-skill>, read directly at commit
`c1c8a8c1471069fb0e188eeaff69b8e8db6564a8` (MIT, Copyright 2025-2026 Cloudflare, Inc.).

## What it actually is

One agent skill, `skills/security-audit/`, that the upstream README describes as the single-repo starting point of
Cloudflare's vulnerability discovery harness. `SKILL.md` runs in two modes. Guidance mode answers security questions and
focused reviews without writing anything. Full audit mode runs only on an explicit audit, pen-test or report request and
drives six phases with isolated agents: reconnaissance into `architecture.md` and `coverage-ledger.json`,
coverage-led hunting, fresh-verifier candidate validation, structured `findings.json` checked against
`report-schema.json`, independent record verification, and a target-neutral `REPORT.md`.

Beside `SKILL.md` sit fourteen phase and domain chapters (`RECONNAISSANCE.md`, `HUNTING.md`, `ATTACK-CLASSES.md`,
`VALIDATION-AND-REPORTING.md`, and companions for web, client-side, cloud, supply chain, memory safety, AI and LLM,
protocols, resource exhaustion, data isolation, desktop and IPC), plus two zero-dependency Node validators,
`validate-findings.cjs` and `validate-coverage-ledger.cjs`, with their own tests.

## What it touches here

The capability is new. `agent-harness/agent-instructions/skills/development/review/SKILL.md:3` covers security risks
inside a diff or a delivery check; nothing here drives a whole-codebase, coverage-ledgered audit with verified,
schema-checked findings. It replaces and deletes nothing.

It lands as the first vendored skill: a pinned upstream tree deployed byte for byte, using the same `fetchFromGitHub`
pin the repo already uses for Wellput in `agent-harness/agent-instructions/wellput-plugin/upstream.nix`.

- `agent-harness/agent-instructions/vendored-skills/upstream.nix` — new; pins the upstream revision and hash and names
  `security-audit` → `skills/security-audit` inside it.
- `agent-harness/agent-instructions/interactive-skill-catalog/skill-set-builders.nix:53-65` — merges vendored skills
  into the catalog and asserts no vendored name shadows an authored one; `:105` deploys a vendored tree as-is for
  clawde agent skill sets instead of through the instruction projection.
- `agent-harness/agent-instructions/production-plugin/artifacts.nix:49` — the complete plugin carries the vendored tree
  unprojected; `:180` records `vendoredSkills` in the artifact inventory.
- `agent-harness/agent-instructions/__tests__/verify-generated-instructions.py:36,76` — exempts vendored trees from this
  repo's instruction-format verifier, which upstream prose (`#`/`##` headings, unwrapped lines) does not and need not
  satisfy. `production-plugin-artifact-preservation` still proves the deployed tree is byte-identical to its source.
- `agent-harness/quality/evaluations/evals/skill_routing.yaml:5` — the generated all-skills description now lists
  `security-audit`; one routing case sends a full-audit request to `all-skills`.

Because it is not in `defaultInteractiveSkillNames`, it reaches every harness only through the all-skills index and the
one plugin bundle that Claude Code, Codex, OpenCode, Pi and Hermes all consume, at
`plugin/library/skills/security-audit/`. No session pays for its description unless it routes there.

## Reasoning

Adopt rather than trial: the skill is self-contained markdown plus two dependency-free validators, so packaging it costs
one pin and no runtime dependency, and guidance mode makes loading it harmless. Vendoring unmodified keeps the upstream
methodology and its validators in lockstep; a rewrite into this repo's instruction format would fork a security
methodology this repo is not positioned to maintain. Bumping is one `rev` and `hash` change.

The vendored-skill path is generic but justified by this first use: the catalog, both deploy paths and the format
verifier each needed exactly one branch, and the next third-party skill reuses them with one line in `upstream.nix`.

The honest cost is that vendored prose is outside this repo's instruction checks, so a bump is reviewed by reading the
upstream diff rather than by the format gate.

## Drafted vault entry

To be written under `Second Brain/` per its CONTRIBUTING contract only after this lands, with the landing commit.

```markdown
---
title: "Cloudflare - security-audit skill"
type: reference
status: filed
source-url: https://github.com/cloudflare/security-audit-skill
creator: Cloudflare
platform: github
captured: 2026-10-19
license: MIT
---

## What it is
Cloudflare's open-sourced agent skill for source-first security audits: guidance mode by default, and a six-phase full
audit (recon, coverage-led hunting, adversarial validation, schema-checked findings, independent verification,
target-neutral report) on explicit request.

## What to steal
- A coverage ledger turns "we looked everywhere" into a checkable claim; a validator rejects the run if it lies.
- Three verdicts kept distinct: confirmed needs a complete trace, needs_validation names the exact unresolved fact and
  carries no severity, rejected records the disproof.
- Every candidate goes to a fresh verifier that tries to disprove it before it is reported.
- Guidance mode by default, so loading the skill never authorizes a long audit by itself.

## Where it lives here
Vendored into the dotfiles all-skills index as `security-audit`, pinned at upstream c1c8a8c1.
```
