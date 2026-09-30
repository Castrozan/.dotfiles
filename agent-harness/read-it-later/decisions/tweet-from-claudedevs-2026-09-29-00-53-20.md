# ClaudeDevs — Eval design and hillclimbing

Capture: `ReadItLater Inbox/Tweet from ClaudeDevs (2026-09-29 00-53-20).md`
Origin: https://x.com/ClaudeDevs/status/2104676099083190435
Resolved article: https://claude.dev/blog/automating-eval-design-and-hillclimbing/
Verdict: **learn**

## The origin as resolved

Read through the twitter skill (`twikit-cli tweet 2104676099083190435`), not a search. The 2026-09-28 post
announces two commands in Anthropic's `claude-api` skill: `build-eval` creates an evaluation for a Claude-powered
application, and `hillclimb` improves an application against one. Its `t.co` link resolves to Lance Martin's
12-minute claude.dev article, whose Markdown version was read directly.

The article's useful claim is narrower than “let an agent optimize itself.” A climb is credible only when the tasks
represent production, stronger models and greater effort behave monotonically, the best configuration retains
headroom, run-to-run variance is smaller than the improvement worth acting on, and the optimizer never sees the held-out
cases. Each round makes one attributable change, keeps it only when both the visible and held-out scores improve, and
reverts regressions or train-only gains.

I also inspected the linked upstream skill rather than inferring its behavior from the article. `claude-api/SKILL.md`
is a broad, Claude-specific API reference of about 100 KB; its `build-eval` and `hillclimb` flows are two parts of that
larger package. The skill is Apache-2.0, but its own routing tells it to stop on OpenAI or provider-neutral targets
rather than modify them with Anthropic SDK code.

## What it touches here

This pull request changes no evaluation code. The learning exercise belongs to the existing agent-evaluation system:

- `agent-harness/quality/evaluations/runner/run_evals_arguments.py:44-63` already exposes repeated epochs and paired
  A/B comparison against a Git ref.
- `agent-harness/quality/evaluations/runner/comparisons/run_evals_ab.py:40-94` alternates candidate/control order and
  evaluates both arms against the same full set.
- `agent-harness/quality/evaluations/runner/sampling/run_evals_significance.py:65-145` already computes a paired
  hierarchical-bootstrap interval and exposes hard-failed cases.
- `agent-harness/quality/evaluations/runner/run_evals_worktree_and_environment.py:13-29` runs the subject inside a
  detached worktree that contains the evaluation corpus itself.

The first three are strong foundations. The last point is the gap: a tuning agent working in that worktree can inspect
every case, so merely labelling part of the current corpus “test” would not make it held out. The current CLI also has
no pre-climb gate for headroom, model/effort monotonicity, or whether the confidence interval is narrower than the
smallest gain worth keeping.

If the exercise succeeds, it would extend these files with a blinded split and an audit gate before any automated
hillclimb. It would replace the manual loop of editing an instruction surface and judging the same complete A/B suite
that informed the edit. It does not replace the runner, provider adapters, judge calibration, repeated sampling,
bootstrap comparison, or committed regression baseline.

## Why learn

Do not adopt the upstream `claude-api` skill wholesale. This repository deliberately evaluates Claude, Codex and
OpenCode, and the local runner already owns the reusable evaluation mechanics. Vendoring a large provider-specific API
manual would duplicate those mechanics, add a rapidly changing documentation surface, and still not solve the local
holdout-leakage problem.

Do not call the existing A/B mode a hillclimber yet either. It can measure a candidate against a control, but every case
is available during diagnosis and every subject receives the repository containing those cases. Automating edits on
top of that would make a train-set improvement look like evidence of generalization.

The thing worth retaining is a practice, with a falsifiable result:

1. Choose one existing instruction category with enough cases and an instruction surface cheap to change.
2. Measure unchanged-baseline variance across repeated runs, the best configuration's headroom, and the paired interval
   width before making an edit.
3. Place a deterministic held-out slice outside the tuning agent's readable worktree. Give the analyzer only training
   transcripts; preserve the validation slice for selecting rounds and the test slice for one final comparison.
4. Make one root-cause edit per round and record the patch, train result, held-out result, token use and wall time.
5. Keep the workflow only if it produces a test-set improvement beyond the predeclared noise floor without weakening a
   non-target metric. Otherwise keep the existing human-directed A/B workflow.

This is a `learn`, rather than a `reference`, because the source exposes a concrete weakness in a live local system and
names an experiment that can disprove the proposed remedy. It is not an `adopt` because the leakage boundary and cost
have not been proven here, and not a `trial` because running the upstream command against this multi-provider repository
would test the wrong integration.

The cost is one bounded evaluation experiment, including repeated model calls, plus the design work needed to keep the
held-out cases structurally unavailable to both the tuning agent and evaluated subject. The exercise earns code only if
that evidence justifies the extra runner surface.

## Drafted vault entry

To be written to `Second Brain/Inspiration/Anthropic - Eval design and hillclimbing.md` only after approval and linked
under `## Notes` in `AI Agent Skills MOC`. `topic/ai-agents` already exists in the Tag Legend; no new tag is needed.

```markdown
---
title: "Anthropic - Eval design and hillclimbing"
type: reference
status: filed
source-url: https://claude.dev/blog/automating-eval-design-and-hillclimbing/
creator: Lance Martin / Anthropic
platform: claude.dev
captured: 2026-09-29
rating: practice
license: reference-only; upstream claude-api skill is Apache-2.0
tags:
  - topic/ai-agents
---
Up: [[AI Agent Skills MOC]]

## What it is

Anthropic's workflow for building an evaluation and improving an LLM application against it one attributable change at
a time. The useful part is not the loop itself but its measurement discipline: production-shaped tasks, visible
headroom, low variance, a grader checked against human judgment, and train/validation/test cases that prevent the
optimizer from mistaking memorization for progress.

## What to practice

- Measure the unchanged baseline's variance before editing. State the smallest improvement worth keeping and require the
  paired interval to be narrower than that threshold.
- Check that stronger models or higher effort improve the score and that the frontier remains below saturation. If
  either fails, investigate ambiguous tasks and grader calibration before optimizing.
- Keep test inputs and answers structurally outside the tuning agent's reach. A field named `test` inside the same
  readable repository is a label, not a holdout.
- Diagnose only training transcripts, make one root-cause change, and revert a change when training improves but
  held-out performance is flat or worse.
- Report the final held-out delta against the original baseline, with token use and wall time. Training improvement is
  search progress, not the result.

## Local exercise

Apply those checks to one category in the existing `agent-eval --ab --compare-ref` workflow. Preserve the current paired
bootstrap comparison, provider adapters and committed baseline. Add no permanent runner feature until a blinded
train/validation/test experiment shows a held-out improvement beyond noise.

## Reuse for

[[AI Agent Skills MOC]]: trustworthy instruction tuning, eval audits, and deciding when an automated hillclimb has
earned its complexity.
```
