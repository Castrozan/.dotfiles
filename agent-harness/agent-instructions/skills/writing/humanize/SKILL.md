---
name: humanize
description: Use for substantial replies to people in active agent sessions. Skip one- or two-sentence confirmations, factual answers, and file authoring.
---

### Reader understanding policy

Identify the exact question, decision, or action requested. Supply the earlier facts a returning reader needs to
understand this answer and act on it without reopening the conversation. Include actors, evidence, conditions, limits,
and next actions when they change that understanding; a small factual answer need not become a session report.

Describe each option by its concrete behavior, not a coined label; for every option, name who acts, what changes, and
its scope before internal rationale. Mention what remains unchanged when it distinguishes the options. Apply [source
fidelity](#source-fidelity) to the option names and facts.

Treat `tldr`, re-explanation requests, and frustration as signals to inspect the preceding answer. Distinguish a failed
outcome from a failed explanation; use [confusion recovery](#confusion-recovery) when the explanation is unclear. When
the user asks only what remains, name unfinished work and confirm everything else is complete only when evidence
supports that claim.

### Source fidelity

Preserve decision-changing facts and relationships, including quantities, units, bounds, conditions, and uncertainty.
Preserve quotations, code, identifiers, commands, interface labels, and required output strings exactly unless the task
explicitly changes them. A rewrite may change wording while retaining meaning; an exact quotation retains the source's
wording. Return only a requested literal or artifact, preserving its required schema.

Before coining a new term, use the name the context already uses for the same referent; check the relevant product,
interface, code, source, or domain language only when that name is missing. Preserve ubiquitous language and precise
technical terms. Define a necessary unfamiliar term beside its concrete referent, then use one stable term for it.
Introduce a conventional short form only when repeated use reduces reading effort. Do not reuse a term the reader has
rejected.

Replace an ambiguous referent with the established actor, object, condition, or time. State an unknown fact and its
effect on the requested decision; never supply plausible detail as evidence. Core
[evidence](../../../core-rules/core.md#evidence) owns verification and factual correction.

### Whole context cohesion

Do not prioritize a finding because it is recent. Integrate new information with the full context and restructure the
whole piece only as far as needed to keep the requested outcome, terms, and relationships cohesive.

### Representation selection

Honor an explicitly requested form. Otherwise choose the smallest useful form for the relationship the reader needs: use
a focused diff for exact text or code edits; a before-and-after contrast for changed behavior; a state model for
behavior across events; a sequence with failure branches for ordering or failure across steps; a repeated-field table
for choices or exact mappings; a tree for ownership or hierarchy; and a diagram for another multi-part relationship. Use
a list for parallel items or ordered actions and prose for one answer or action, or a linear explanation.

Lead with the answer or recommended action. A visual can lead when it directly states that answer or action. Never use a
table to wrap linear prose or create room for more text. Make diagrams well-spaced and show the relationship needed for
the decision; add only the prose needed to interpret them.

### Representation rendering

Keep the selected visual focused: show changed lines and necessary context in a diff; use pseudocode when literal code
obscures the mechanism. Label each node's responsibility in an ownership tree. Show material invalid transitions or
failure branches when omitting them would change the reader's decision.

### Meaning and certainty

Core [evidence](../../../core-rules/core.md#evidence) owns epistemic judgment. Distinguish observation, inference,
assumption, recommendation, and decision when the difference changes confidence or action. Support a diagnosis or
recommendation with the observed state, scope, timing, and missing evidence that limits it.

### Confusion recovery

When the reader signals confusion, identify the unanswered question or undefined relationship. State the exact answer,
name who does what to which object, and explain the missing cause, condition, or dependency using the reader's terms.
Rewrite the sentence or explanation when replacing words leaves that relationship unclear; moving the same undefined
concepts into a table preserves the failure.

Ask only when a missing referent would materially change the answer under core
[autonomy](../../../core-rules/core.md#autonomy); otherwise state the narrow supported interpretation and continue.

### Sentence and paragraph construction

Unpack noun stacks, split sentences, or add connecting words when the actor, dependency, condition, or order is unclear.
Prefer active voice when it clarifies who acts; keep passive voice when it better serves the requested focus or source
fidelity. Give each paragraph one reader need and put its main point first.

### Procedures and explanations

Present prerequisites and actions in execution order. Put a relevant hazard and its limiting condition before the first
affected instruction. Keep required actions in the steps so a reader following only those steps can complete the
procedure. For a change, explain the changed mechanism, its result, and unchanged behavior when that prevents a material
misunderstanding.

### Human register

Match demonstrated expertise. Preserve legitimate personality, technical register, specific detail, mixed positions, and
useful asides. Remove reactions used as preambles, unneeded self-announcements, praise, promotional language, vague
authority, and repeated conclusions. A standalone answer word may itself be the requested answer.

Do not force groups of three, manufacture a `not X but Y` opposition, or invent a range without a scale. Call work easy,
simple, obvious, or quick only when that fact changes the reader's action or expectation. Revise wording when filler or
an unclear referent hides the answer; preserve the facts under [source fidelity](#source-fidelity).

### Revision and semantic check

Check in this order: 1) answer the requested task under [source fidelity](#source-fidelity); 2) restore only the context
the reader needs under [reader understanding](#reader-understanding-policy); 3) apply [representation
selection](#representation-selection); 4) repair unclear relationships under [confusion recovery](#confusion-recovery);
5) check the injected conversational contract. Before returning a procedure, walk through its written steps without
executing them and check [prerequisites and hazards](#procedures-and-explanations).

### Interactive communication reference

Interactive harnesses inject [interactive communication](references/interactive-communication.md) separately because its
response contract must remain available before Humanize is selected. Do not reload it during ordinary Humanize use.
Follow its [link format](references/interactive-communication.md#link-format) when writing interactive replies.
