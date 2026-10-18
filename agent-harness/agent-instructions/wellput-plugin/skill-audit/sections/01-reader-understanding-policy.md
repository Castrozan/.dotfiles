# Reader understanding policy: sentence audit

Sentence IDs S01-S08. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#reader-understanding-policy).

## Section assessment

Keep the reader-recovery goal and the two specialized behaviors: explain unresolved choices concretely, and answer 'what
remains' without replaying history. S2, S3, and S8 currently restate the goal at different levels, while S5 adds a
potentially compulsory heading/schema. Consolidation must preserve the choice and remaining-work controls rather than
deleting the section as generic writing advice. Its relationships with fidelity and representation should form a
priority order: identify the requested result, preserve its meaning, then choose the presentation.

Most useful content: S1, S5, and S7. Main repair: make context conditional and clarify that explicit requested output
forms outrank presentation defaults. See F01, F03, and F06 in the main audit.

## S01: Keep

> Identify the exact question, decision, or action requested.

**Assessment:** This is the correct entry rule: the requested question or decision determines relevance before style or
format. It is observable enough to review against the user request. The missing boundary is that later defaults never
explicitly yield when the user already supplied an exact output form; the hook probes show why the boundary matters.

**Related:** S18 and S61 must consume this decision; S27 should express it in the answer. The injected concise-request
rule is the closest existing precedence owner.

**Recommendation:** Keep the intent. Add one shared task-and-format precedence rule rather than repeating an exception
in every stylistic sentence.

**Principles:** Task fit; instruction precedence.

## S02: Merge

> Optimize for a multitasking reader recovering the requested outcome and relationships needed to act without prior
> history.

**Assessment:** The goal of supporting a multitasking reader is essential, but this sentence states an optimization
objective rather than a distinct drafting operation. 'Without prior history' can mean that the reader need not reread
history or, incorrectly, that the agent should ignore it. Only the first meaning fits the rest of the policy.

**Related:** S3 defines the same outcome, S8 repeats standalone readability, S17 requires integrating prior context, and
S64 repeats the context inventory for artifacts.

**Recommendation:** Keep one reader-recovery objective: supply the earlier facts needed for the current answer without
requiring the reader to reopen the conversation.

**Principles:** Density; referent clarity.

## S03: Narrow

> Success means that the reader can identify the answer, actor, evidence, conditions, limits, and required next action
> without needing to go back through the conversation history.

**Assessment:** The six-part success inventory can become a mandatory report schema even for a small question. Evidence,
limits, actor, and next action are useful when they affect a decision, not obligatory material in every factual answer.
The existing small-question evaluation explicitly expects a single path without rationale or next-step padding.

**Related:** S2 and S8 share the objective; S28 owns evidential qualification; S61 repeats this inventory. The
interactive contract already limits session retelling.

**Recommendation:** Make these conditional review questions, or replace the inventory with 'Can the reader identify the
answer and act on it without missing decision-changing context?'

**Principles:** Density; proportionality; conditional scope.

## S04: Merge

> When asking the reader to choose, apply `[source fidelity](#source-fidelity)` and `[confusion
recovery](#confusion-recovery)` before naming the options.

**Assessment:** The ordering constraint is useful, but linking the whole confusion-recovery section for every choice is
too broad: an ordinary first-time choice does not imply a failed preceding explanation. The reader must also resolve two
cross-references before reaching the concrete rule in S5.

**Related:** S5 contains the actionable choice contract. S10 and S14 supply established terms and referents; S29 is a
recovery trigger rather than a universal choice prerequisite.

**Recommendation:** Put the concrete choice rule in one paragraph. Apply recovery only when the reader has actually
signaled misunderstanding.

**Principles:** Progressive disclosure; scope; pointer precision.

## S05: Keep and narrow

> Use each option's concrete behavior, not a coined label, as its heading; for every option, name who acts, what
> changes, its scope, and what remains unchanged before internal rationale.

**Assessment:** This is one of the strongest specialized rules: it describes the actor, behavioral alternatives, scope,
and order needed for an unresolved choice. However, requiring every option to be a heading can overformat a two-line
answer, and requiring unchanged behavior every time can add a repetitive field with no decision value.

**Related:** S1 establishes the choice; S10 supplies domain vocabulary; S14 resolves referents. The ownership test pins
several exact phrases, and the provisioner evaluation protects the substantive behavior.

**Recommendation:** Keep concrete behavior before internal rationale. Permit a heading, row, or sentence, and name
unchanged behavior when it distinguishes the options or prevents a material misunderstanding.

**Principles:** Observable behavior; proportionality; ownership.

## S06: Keep and narrow

> Treat `tldr`, re-explanation requests, and frustration as signals to inspect the preceding answer.

**Assessment:** Inspecting the preceding answer is a useful response to a TL;DR request or frustration. Inspecting is
not the same as assuming that the language caused the frustration. A failed deployment can provoke anger even when the
explanation was clear; the existing operational-anger control already protects that distinction.

**Related:** S29 only triggers after a confusion signal. S31-S33 define actual recovery; the operational-anger
evaluation supplies disconfirming evidence against an unconditional 'frustration means bad writing' reading.

**Recommendation:** Retain the inspection trigger and make the diagnosis explicit: identify whether the problem is
length, missing referents, an unanswered decision, or the underlying outcome.

**Principles:** Named failure; trigger precision.

## S07: Keep

> When the user asks only what remains, name the unfinished work and collapse completed work into an explicit
> confirmation that everything else is complete.

**Assessment:** This has a concrete trigger and a concrete observable response, and it is backed by a dedicated
evaluation. It prevents an attention-costly replay of completed history. The confirmation that everything else is
complete is safe only when the session evidence actually supports that claim.

**Related:** S1 limits the response to the user's current question. Core Evidence owns whether completion is
established; the mandatory session label must not force a second history recital.

**Recommendation:** Keep the rule and its evaluation. Preserve 'only' and the evidence requirement; do not turn the
confirmation into an inventory of completed work.

**Principles:** Task fit; evidence ownership.

## S08: Merge and narrow

> Write text that must stand alone so a reader without the agent session can understand it without additional session
> context.

**Assessment:** Self-contained writing is the central outcome, but 'a reader without the agent session' can imply an
entirely new reader rather than the actual user returning to this task. That interpretation encourages excessive
background. The injected policy already states the narrower boundary: supply the earlier fact on which the current
question depends.

**Related:** S2-S3 state the same recovery goal, S64 applies it to artifacts, and the interactive-contract tests
explicitly reject retelling the whole session.

**Recommendation:** Merge with S2-S3 around task-dependent context. Keep separate artifact audience guidance only where
its reader actually differs from the conversational user.

**Principles:** Density; audience scope.
