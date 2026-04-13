---
name: review
description: Quality, review, and output craft — unbiased code review rubric for reviewer subagents, offloaded-rule compliance auditing, documentation policy, skill and instruction authoring, ultra-dense output mode. Use when reviewing code, auditing rule compliance, writing docs or policies, designing skills or prompts, or when the user asks for compressed responses.
---

Umbrella skill for review, compliance, documentation, instruction authoring, and output density. Each capability lives in its own file so only the one you need loads into context.

For unbiased code review by a reviewer subagent — bug/security scanner, conventions checker, 81+ confidence scoring — read `code-review.md`.

For compliance auditing of offloaded rules (python-over-bash, test-first, local-info-first, investigation depth) against a diff and tool sequence — read `compliance.md`.

For documentation policy — naming over docs, evergreen vs stale, when docs are needed, policy versus instruction boundary — read `docs.md`.

For skill and instruction authoring — skill format, description-driven discovery, evergreen patterns, routing diagnosis, preflight checklist — read `authoring.md`.

For skill routing diagnosis when a skill exists but the model bypasses it — read `skill-routing.md`.

For ultra-dense output mode (30% normal verbosity, lead with the answer, no preamble) — read `tldr.md`.
