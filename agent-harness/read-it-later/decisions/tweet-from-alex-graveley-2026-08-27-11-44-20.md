# Alex Graveley on cyclomatic complexity as an agent constraint

Capture: `ReadItLater Inbox/Tweet from Alex Graveley (2026-08-27 11-44-20).md`
Origin: https://x.com/alexgraveley/status/2092647694816707042
Linked comparison: https://x.com/bentlegen/status/2092606355685216425
Verdict: **adopt**

## The origin as resolved

Read through the twitter skill, starting from the capture's own first link. `twikit-cli tweet` and `thread` resolve the
captured post as a single tweet by Alex Graveley: "Just tell the LLM it has to pass cyclomatic complexity lint and it
will write simpler code." The post's shortened link resolves to Ben Vinegar's comparison, titled "how cyclomatic
complexity audits can fix your slop code drops from 91 decision paths to 12". Twikit's parser fails on that linked post,
so its text and media were recovered from the exact X page through the unattended browser fallback and its Open Graph
image, rather than reconstructed from a topic search.

The linked image is a TypeScript diff. It replaces a four-arm `if`/`else if`/`else` tree, including repeated ternaries,
with two direct assignments. The visible excerpt shrinks from 25 lines to four. The source demonstrates one successful
rewrite; it does not identify the model, linter, threshold, prompt, repository, or test result behind the claimed
91-to-12 reduction. Replies supply anecdotes and tool names, not a controlled comparison.

## What it actually is

A steering heuristic backed by a deterministic constraint: an agent asked to satisfy a branch-count limit has a reason
to collapse redundant control paths instead of preserving every case it first generated. Cyclomatic complexity counts
independent control-flow paths. It is useful for flat decision trees that cognitive complexity can underweight, but it
does not prove cohesion or correctness and can be gamed by splitting branches across helpers.

The durable part is the gate, not the prompt wording. This repository's instruction authority already says to enforce
precise predicates with deterministic code at `agent-harness/agent-instructions/core-rules/core.md:66-72`, while its
coding rule already asks for cohesive units and direct control flow at
`agent-harness/agent-instructions/core-rules/core.md:50-53`. Adding another prose instruction would duplicate both.

## What it touches here

`repository/verification/quality/sonarqube/cloud.json:33-89` is the existing policy owner. It already inherits Sonar's
comprehensive Python, JavaScript and TypeScript profiles. This change activates their native cyclomatic-complexity
rules with the upstream defaults:

- `python:FunctionComplexity`, maximum 15;
- `javascript:S1541`, maximum 10;
- `typescript:S1541`, maximum 10.

The exact rules were queried from the configured Sonar organization before editing. All three are `READY`, `CRITICAL`
rules, and none was active in the project's `Dotfiles` profiles. The inherited profiles already activate cognitive
complexity rule `S3776`; the two measures are complementary rather than aliases.

The change reuses the existing quality gate at `repository/verification/quality/sonarqube/cloud.json:7-30`, which
allows zero new violations, and the existing CI policy apply plus scan at `.github/workflows/tests.yml:122-134`.
`sonar-project.properties:18-19` already waits for the gate result. It adds no package, hook, service, prompt rule or
second analyzer. It replaces and deletes nothing.

Coverage remains deliberately bounded. Sonar has native cyclomatic rules for the three configured languages, but none
for this project's shell profile, and Sonar does not analyze the repository's Nix, QML or Lua with native language
rules. The existing cognitive-complexity findings remain technical debt; this gate prevents new violations rather than
claiming to simplify old code automatically.

## Reasoning

**Adopt.** The source names a precise property, this repository already owns its enforcement in Sonar, and the exact
rules are the missing extension point. Activating those rules is stronger and cheaper than telling every agent to
imagine a linter: all harnesses receive the same pass/fail result, humans receive it too, and the policy stays declared
beside the existing quality profiles.

The alternatives are weaker here. A new Ruff or ESLint job would duplicate the scanner and cover a different subset of
the same languages. A prompt-only instruction would be unverifiable before review and duplicate the core's cohesion
guidance. Treating the tweet as a learning item would preserve a technique while leaving the available deterministic
gate off.

Cost is one additional critical rule per supported language. A newly changed function over the threshold can fail CI
and require a real control-flow simplification or a separately reviewed profile change. The check can reward mechanical
function splitting, so it remains a bound on paths, not a substitute for tests or design review.

## Drafted vault entry

After approval, save the linked comparison image as
`Second Brain/Inspiration/_attachments/ben-vinegar-cyclomatic-complexity-diff.webp`, add the note below at
`Second Brain/Inspiration/Alex Graveley - Cyclomatic complexity as an agent constraint.md`, and link it under
`## Notes` in `Second Brain/Atlas/Developer Tooling MOC.md`.

```markdown
---
title: "Alex Graveley: cyclomatic complexity as an agent constraint"
type: reference
status: filed
source-url: https://x.com/alexgraveley/status/2092647694816707042
creator: Alex Graveley
platform: X
captured: 2026-08-27
rating: 4
license: reference-only
palette: []
tags:
  - topic/dev-tools
---
Up: [[Developer Tooling MOC]]

![[ben-vinegar-cyclomatic-complexity-diff.webp|400]]

## What it is

An agent steering pattern with a deterministic backstop: require generated code to pass a cyclomatic-complexity rule,
so redundant decision paths become a failing check rather than a subjective review comment. Alex Graveley links Ben
Vinegar's TypeScript example, where a branch tree with repeated assignments collapses to two direct expressions; the
post claims the larger audit reduced 91 decision paths to 12, but does not provide the model, threshold or tests.

## What to steal

- Convert a desired code property into a real gate when its predicate is precise. The linter result steers the agent
  during revision and gives every reviewer the same boundary.
- Use cyclomatic and cognitive complexity together. Branch count catches flat path explosion; nesting-weighted cognitive
  complexity catches code that is difficult to follow even when it has fewer independent paths.
- Treat the metric as a bound, not the design. Splitting branches into helpers can lower a score without improving
  ownership, side effects or correctness, so behavioral tests and cohesion review still decide whether the rewrite is
  good.

## Adopted

Activated Sonar's native cyclomatic-complexity rules for Python, JavaScript and TypeScript in the dotfiles quality
profiles. Python uses the upstream maximum of 15; JavaScript and TypeScript use 10. The existing zero-new-violations
quality gate enforces them in CI without a new analyzer or agent instruction.

Landing commit: `TO_BE_REPLACED_AFTER_MERGE`

## Reuse for

[[Developer Tooling MOC]]: deterministic constraints for agent-written code, Sonar quality gates and complexity review.
```
