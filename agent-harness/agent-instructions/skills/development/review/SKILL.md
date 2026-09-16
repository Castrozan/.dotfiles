---
name: review
description: Review code, configurations, AI instructions, or completed work for actionable defects, regressions, security risks, and compliance gaps. Use when inspecting a diff, auditing an instruction surface, or verifying delivery.
---

### Core authority

Core [evidence](../../../core-rules/core.md#evidence), [completion](../../../core-rules/core.md#completion), and
[coding](../../../core-rules/core.md#coding) own persistent judgment, verification, and code-quality defaults. This
skill owns the bounded read-only review method, finding contract, severity, and requested-goal verdict.

### Scope

Start with the requested artifact and its intended behavior. Review is read-only unless the user explicitly asks for a
fix. Report only evidence-backed findings in changed code or behavior the change directly affects, not pre-existing
unrelated defects or personal style preferences.

### Method

Read the request, diff, surrounding callers, tests, and relevant invariants before judging. Trace each changed path
through realistic inputs, failure states, ordering, concurrency, resource use, security boundaries, and downstream
consumers. Verify a claim with code, tests, documentation, or a reproducible scenario before reporting it.

### Findings

Each finding states severity, file and line, the concrete triggering scenario, observed consequence, and required
change. Use P0 for release-blocking or destructive failures, P1 for high-priority defects, P2 for ordinary fixes, and P3
for bounded improvements. Omit speculative or non-actionable concerns. If no material finding remains, state "No
findings."

### Goal verification

Verify delivery against the user's own words, not the implementer's summary. Mark every stated requirement met or not
met with the evidence that settled it; the requirement nobody translated into a test is the most likely unmet. Judge the
quality no test can measure: design soundness, cohesion, naming, and whether the shape matches the intent. Name what
should have stayed identical and judge whether the change leaked into it. Report evidence-backed findings with a closing
verdict on whether the goal is achieved; never repair.

### Specialized audits

Read [dotfiles change](references/dotfiles-change.md) for the pre-push dotfiles change-review procedure,
[compliance](references/compliance.md) for end-of-turn policy checks, [authoring](references/authoring.md) for AI
instruction surfaces, and [skill routing](references/skill-routing.md) for skill reachability or routing failures. Use
`docs` for documentation standards and `humanize` for human-facing prose.
