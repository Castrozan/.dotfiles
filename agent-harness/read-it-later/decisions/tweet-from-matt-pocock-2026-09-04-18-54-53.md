# Tweet from Matt Pocock — HumanLayer `show-me` skill

Capture: `ReadItLater Inbox/Tweet from Matt Pocock (2026-09-04 18-54-53).md`
Origin: https://x.com/mattpocockuk/status/2095460192871698728
Linked source: https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md
Verdict: **drop**

## The origin as resolved

Read the captured status and its self-thread through the Twitter route, not a search for the topic. Matt Pocock's
2026-09-03 post calls `/show-me` a toolbox of pleasant ways to look at code and says it makes pull-request descriptions
easy to read. Its first link resolves to HumanLayer's `show-me` skill. A self-reply adds an image of the result but no
further method or claim.

The GitHub link targets mutable `main`. At the time of the post, the latest version was commit
`6ab9013a10c28f5046f7f999549cd5328a0b30d7`; the current file has the same body and adds only
`disable-model-invocation: true`, making the skill explicitly user-invoked.

## What it actually is

A short instruction skill, not a rendering tool or dependency. It asks the agent to choose the smallest useful
visual for the current explanation and supplies examples for pseudocode, call trees, component trees, responsibility
trees, Mermaid sequences, structural diffs, complete code blocks and a one-file HTML artifact. The implementation is
entirely prompt guidance; its only action-specific example opens an HTML file with `Bash(open ...)`.

The useful idea is representation selection: make ownership, order, control flow or change visible when prose would
hide the relationship. The examples help a model render that idea, but they add no capability unavailable to a model
that already has the same selection policy.

## What it touches here

Nothing should change. The existing `humanize` skill already owns representation selection at
`agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:41-59`. It chooses a focused diff for change, a state
model for behavior, a sequence for ordering and failure, a table for repeated fields, a responsibility tree for
hierarchy, a diagram for other multipart relationships, and pseudocode where it expresses the change more clearly.

That skill is already on every interactive surface through
`agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix:16-34`. Its behavior is not only
declared: `agent-harness/agent-instructions/skills/writing/humanize/__tests__/evals/reader_recovery.yaml:267-279` requires
a compact flow that exposes both authentication branches. For architecture-specific diagrams,
`agent-harness/agent-instructions/skills/development/architecture/SKILL.md:26-30` further limits diagrams to ones that
settle ordering, dependency or lifecycle questions.

Adding `show-me` would therefore create a second owner for the same response-format decision. It would replace or
delete nothing, while its HTML-opening instruction assumes a command and presentation path that are not portable
across the repository's Linux, macOS and multiple-agent surfaces.

## Reasoning

Drop this capture. The external skill is a good compact example of a policy this repository already implements more
systematically: the local policy selects formats by relationship, is globally available without an extra invocation,
has an architecture-specific constraint, and has evaluation coverage. Copying the examples into another skill would
increase prompt surface and let two instructions drift without unlocking a new result.

The only material delta is focused HTML artifact authoring. That is a different capability with different ownership,
browser-opening and lifecycle questions; one `Bash(open ...)` example is not enough evidence to define it here. If a
future capture demonstrates a repeatable HTML explanation workflow that the current diagram and document surfaces
cannot express, evaluate that workflow on its own rather than retaining this overlapping skill as a reference.

## Drafted vault entry

None. A drop creates no vault entry.
