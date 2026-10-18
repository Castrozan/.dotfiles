# Procedures and explanations: sentence audit

Sentence IDs S48-S54. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#procedures-and-explanations).

## Section assessment

Preserve prerequisites, execution order, hazard placement, and step completeness. These have clear operational
consequences, unlike a purely stylistic preference. The writing skill should make a procedure usable without assuming
authority to execute it. The list-selection rule is misplaced here relative to the earlier representation chooser, and a
natural six-item answer to the actual six-action evaluation is rejected by the production five-line cap.

Most useful content: S48-S51. Main repair: reconcile the composed list contract, make hazards conditional, and clarify
the procedure walkthrough. See F01, F02, and F07.

## S48: Keep

> Present prerequisites and actions in execution order.

**Assessment:** This is a compact procedural invariant with a clear effect: a reader should not discover a prerequisite
after trying the dependent step. It is ordinary advice, but its operational consequence and existing recovery-procedure
evaluation justify retaining it.

**Related:** S49 orders hazard information, S51 protects step completeness, and S63 checks the resulting procedure.

**Recommendation:** Keep as the procedure section's first operation. Preserve the supplied dependency order even when
the output must stay short.

**Principles:** Observable operation; justified constraint.

## S49: Make the hazard conditional

> Put the hazard and its limiting condition before the first instruction about the affected action, including a
> prohibition.

**Assessment:** The placement requirement is useful when an action has a real material hazard. The definite phrase 'the
hazard' can encourage a warning preamble even for routine steps if the model assumes every procedure needs one. A
prohibition is itself an instruction, so the hazard and the forbidden action must remain understandable together.

**Related:** S48 orders prerequisites; S51 keeps required material in the operative steps. The broader interaction
policy already rejects invented or unnecessary warnings.

**Recommendation:** If a step has a material hazard, state that hazard and its condition before the affected step. Do
not manufacture a hazard to fill the pattern.

**Principles:** Conditional scope; avoid over-warning.

## S50: Delete as duplicate rationale

> A warning after that instruction arrives too late.

**Assessment:** This explains why S49 exists but does not add a condition or behavior beyond putting the warning before
the action. A short rationale can be valuable for surprising rules; here the consequence is already apparent in the
preceding instruction.

**Related:** S49 fully carries the placement requirement; S63 verifies that prerequisites and hazards appear at the
first affected action.

**Recommendation:** Remove this standalone sentence, or keep the reason within S49 only if a controlled comparison shows
the explanation helps adherence.

**Principles:** Density; necessary rationale.

## S51: Keep and clarify

> Keep required actions out of notes and make a procedure complete for a reader who follows only its steps.

**Assessment:** This is a concrete completeness test: a required action hidden in a note can be missed by a reader
following the numbered steps. 'Complete' should be bounded to the requested procedure and known prerequisites rather
than expanded into an exhaustive operational manual.

**Related:** S48 sets dependencies, S49 sets hazard placement, and S63 supplies a walkthrough. Core task scope still
controls which actions are authorized or relevant.

**Recommendation:** Keep required actions and prerequisites in the steps themselves; link optional explanation
separately.

**Principles:** Procedural correctness; task scope.

## S52: Move into representation selection

> Use a vertical list for parallel items, alternatives, prerequisites, or ordered actions when prose would hide their
> relationships.

**Assessment:** This is the policy's explicit support for lists, but it appears well after S18's ordered representation
algorithm. Parallel items, ordered actions, and repeated-field mappings overlap without a shared choice criterion. More
importantly, the injected five-line list ceiling rejects a natural six-item response to the existing six-action
procedure evaluation.

**Related:** S18 owns selection, S48 owns order, and the actual six-step Stop probe demonstrates competing cross-surface
constraints; combining two actions in one item is possible, so the contract is not logically unsatisfiable. The
representation test only checks that bullets are not banned.

**Recommendation:** Move list selection beside the other representations. Preserve required steps and resolve the
list-limit exception in the mechanical owner, not by deleting an action.

**Principles:** Canonical ownership; composed contract correctness.

## S53: Narrow and merge ordering

> For descriptions, move from the answer or known context to the new mechanism and consequence.

**Assessment:** The progression from known context to mechanism and consequence is a useful explanatory pattern. It can
add unnecessary mechanisms or consequences when the user asked only for a fact or a decision. It also competes with
three other ordering rules unless the task defines which information is needed.

**Related:** S1 defines the question, S27 leads with action, S20 orders visuals, and S46 leads with a paragraph's main
point.

**Recommendation:** Start with the requested answer or known premise; add the mechanism and consequence only when they
are needed to understand that answer.

**Principles:** Task-dependent scope; answer-first ordering.

## S54: Keep with materiality

> For a change, name the changed mechanism, the result it caused, and the important behavior that remained unchanged.

**Assessment:** Connecting a changed mechanism to its observed result is useful, especially in an engineering handoff.
The unchanged-behavior clause already says 'important', so this is not an unconditional requirement to invent
reassurance. That qualification should be made operational to avoid another mandatory three-part schema.

**Related:** S5 describes unchanged scope when comparing choices, S13 preserves material facts, and Core Completion owns
the evidence for non-regression.

**Recommendation:** Explain the result and its cause; mention preserved behavior when it addresses a real regression
concern or a misleading inference.

**Principles:** Evidence; proportionality; avoid schema inflation.
