# Representation selection: sentence audit

Sentence IDs S18-S21. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#representation-selection).

## Section assessment

Keep selection guidance but replace the brittle first-match interpretation with reader-need criteria and an explicit
requested-format boundary. The existing branches overlap, and 'sequence' is underdefined. Lists are already supported in
S52, so the defect is distributed ownership and arbitration, not total absence of list support. Mechanical acceptance of
a structure also does not establish whether it is a suitable representation.

Most useful content: the mapping ideas and the anti-prose-table boundary. Main repair: representation fit before
word-budget optimization, and answer/action precedence before incidental visual placement. See F01-F03 and F09.

## S18: Replace the rigid ordering

> Choose the smallest useful form with this first-match procedure: 1) for change against an existing shape, use a
> focused diff; 2) for the same mechanism before and after a change, use a compact before-and-after contrast; 3) for
> behavior across events, use a state model with material invalid transitions; 4) for ordering or failure across
> steps, use a sequence with material failure branches; 5) for a repeated-field comparison of choices or exact
> mappings, use a table; 6) for ownership, hierarchy, or nesting, use a tree with each node's responsibility; 7) for
> another multi-part relationship, use a diagram; 8) for one answer or action, or a linear point, use prose.

**Assessment:** The first-match list mixes topic, relationship, and output type. A mechanism before-and-after is also a
change against an existing shape, so the earlier diff branch can shadow the comparison branch. 'Sequence' is ambiguous
between an ordered account and a sequence diagram, and ordered lists are only introduced much later. These are static
decision ambiguities, not evidence that a model always chooses incorrectly.

**Related:** S1 supplies the task; S22-S23 repeat two mappings; S52 adds lists; the concise-request policy treats named
representations as binding. Existing representation tests require the mappings and anchor.

**Recommendation:** Honor an explicit requested form first. Otherwise choose by the relationship the reader must
recover, with nonexclusive examples and a fit check rather than a generic first-match precedence.

**Principles:** Branch clarity; instruction precedence; progressive disclosure.

## S19: Keep

> Never use a table to wrap linear prose or create room for more text.

**Assessment:** This names a concrete failure: linear prose concealed in a table. The live checker accepts a 250-word
paragraph inside an indexed cell, proving that mechanical acceptance does not establish this rule. Detecting whether
prose is merely disguised is a semantic judgment and should not be replaced by a brittle table-size regex.

**Related:** S21 states the purpose of visuals; S24 limits duplicate explanation; the budget checker excludes table
lines and its repair feedback suggests structural alternatives.

**Recommendation:** Keep this semantic boundary and add a composed evaluation for prose hidden in a table. Make repair
feedback preserve representation suitability rather than optimize only the counted word total.

**Principles:** Instruction versus enforcement; named failure.

## S20: Narrow

> Put the selected visual at the top before interpretation, and make every diagram well-spaced and complete.

**Assessment:** 'Put the selected visual at the top' is an absolute ordering rule, while S27 requires the recommended
action first. The conflict can be avoided when the visual itself carries the action, but no tie-breaker says what to do
when it does not. Diagram spacing and completeness are also separate concerns bundled into this sentence.

**Related:** S27 and S1 favor the answer or decision first; S18 chooses the representation; the representation test
currently pins 'well-spaced' in this section.

**Recommendation:** Lead with the answer or requested action; place the visual before any explanation needed to
interpret it. Keep diagram readability as a separate rendering check.

**Principles:** Priority arbitration; one concern per sentence.

## S21: Keep and combine

> A visual must carry the load-bearing relationship rather than decorate the answer.

**Assessment:** This is useful judgment: a diagram earns its place by showing the relationship that matters. It is not
defective merely because it is wisdom rather than a deterministic action. 'Load-bearing relationship' is unnecessarily
architectural jargon inside a skill that warns against invented abstraction.

**Related:** S18 selects by relationship, S19 prevents decorative table use, and S24 limits explanatory duplication.

**Recommendation:** Keep the criterion in plain terms: 'Use a visual only when it makes the relevant relationship easier
to understand.'

**Principles:** Useful rationale; terminology; density.
