# Representation rendering: sentence audit

Sentence IDs S22-S24. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#representation-rendering).

## Section assessment

A rendering section can add value after a representation has been selected. Here two of its three sentences repeat
selection decisions, while S24 adds the useful check against explaining the same relationship twice. Retain the
how-to-read and how-to-label details, and consolidate the decisions about whether to choose a diff, tree, or table in
one place.

Most useful content: S24 and the responsibility-label detail of S23. Main repair: separate choice from rendering and
distinguish conceptual ownership diagrams from directory snapshots. See F03, F06, and F08.

## S22: Merge

> Show additions and removals in a focused diff; use source text or pseudocode when either expresses the change more
> clearly.

**Assessment:** This repeats the first branch of S18 almost verbatim, then adds the useful option of source text or
pseudocode. A diff is appropriate for changed text or code, but not automatically for every conceptual or operational
change.

**Related:** S18 should own the selection criteria. This section can own only how to keep a chosen diff focused and
faithful. The representation test currently requires pseudocode here.

**Recommendation:** State the diff choice once. Keep a short rendering rule for the necessary surrounding context, exact
changes, and readable labels.

**Principles:** Single ownership; task-dependent representation.

## S23: Narrow and reconcile

> Render sibling ownership paths under their common parent and label each responsibility in the tree rather than
> describing the paths only in prose.

**Assessment:** The ownership-tree rendering rule is concrete and helps expose parent-child responsibility. A flat
ownership mapping may be clearer as a table, so the tree should not be compulsory whenever paths are mentioned. The
artifact-writing reference also broadly bans directory and structure snapshots; that overlaps when these 'paths' are
literal filesystem paths.

**Related:** S18 supplies the tree mapping, S65 imports the artifact policy, and S1 determines whether the relationship
is hierarchical or merely a mapping.

**Recommendation:** Use trees for actual hierarchy and identify node responsibility. Distinguish a useful ownership
diagram from a transient directory listing, including in artifact guidance.

**Principles:** Scope; cross-file consistency.

## S24: Keep and consolidate

> Add only prose needed to interpret the visual; repeating the same relationships in prose increases load without
> adding meaning.

**Assessment:** The instruction is observable and its rationale explains a recurring reading-cost failure. It overlaps
with S21 but serves a different stage: a useful visual can still be followed by a redundant paragraph. Some prose is
needed to state a conclusion or explain how to read the visual, so elimination should be based on added information.

**Related:** S21 judges the visual; S27 can require an action caption; S61 can perform the duplication check during
revision.

**Recommendation:** Keep one rendering check: add only the conclusion, qualification, or interpretation the visual does
not already convey.

**Principles:** Density; justified rationale.
