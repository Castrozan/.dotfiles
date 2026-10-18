# Source fidelity: sentence audit

Sentence IDs S09-S15. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#source-fidelity).

## Section assessment

Retain this as a canonical meaning-preservation owner. The section contains useful safeguards for exact identifiers,
source facts, ambiguity, and unknowns. Its main defect is that exact quotation and preservation of meaning are not
separated from legitimate editing or correction. Terminology rules in a later section repeat this owner. Removing those
repeated commands is different from deleting fidelity: the factual and referent invariants must remain explicit.

Most useful content: S10 and S13-S15. Main repair: scope exactness to the task, merge terminology, and keep truth
verification with the epistemic owner. See F04 and F06.

## S09: Narrow

> Preserve exact facts, identifiers, original text, code, interface labels, domain terms, numbers, conventional
> concepts, names, and ubiquitous language.

**Assessment:** The preservation inventory protects meaning and technical accuracy, but 'Preserve exact ... original
text' is ambiguous during a requested rewrite, translation, correction, or rename. Exact quotations and identifiers are
not the same kind of invariant as revisable prose. Without an explicit boundary, faithfulness can conflict with the very
editing task that invoked the skill.

**Related:** S11 authorizes rewriting; S12 protects precise terms; S13 protects material information; S39 repeats
technical literals. Core Evidence also requires correction when facts are challenged.

**Recommendation:** Define fidelity once: preserve facts and established referents, preserve exact strings where
required, and change wording or content only as the task explicitly requires.

**Principles:** Task scope; precision; density.

## S10: Keep and consolidate

> Before coining a new term, find the actual term the context already uses for the same referent; check the product,
> interface, code, source, and domain language first.

**Assessment:** Looking for the existing domain term before inventing one directly prevents the observed opaque-label
failure. 'Check the product, interface, code, source, and domain language' should not become a requirement to search all
five surfaces when the supplied context already establishes the term.

**Related:** S35 points back here, S36 handles the no-existing-name case, S38 requires consistency, and S31 handles a
term the reader rejected. Wording and behavior are covered by existing tests.

**Recommendation:** Make this the canonical terminology owner. Search the relevant available source only when the
context does not already name the referent.

**Principles:** Single ownership; bounded action.

## S11: Keep and clarify

> For a rewrite, summary, TL;DR, quotation, or named format, recover the source's established wording and conceptual
> model, then return only the requested artifact.

**Assessment:** The trigger and requested-artifact-only behavior are useful. 'Recover the source's established wording
and conceptual model' leaves open how much wording may change in a rewrite and how to handle an error in the supplied
source. A faithful quotation, a factual summary, and an editing request need different preservation boundaries.

**Related:** S9 must distinguish exact text from meaning. S15 handles unknown facts; Core Evidence handles factual
correction. The short-answer and channel evaluations protect output-only behavior.

**Recommendation:** Keep the task-specific instruction and state that the requested transformation controls which
wording may change; separate quotation from factual correction.

**Principles:** Task scope; fidelity; evidence boundary.

## S12: Merge

> Keep a precise technical term when a familiar substitute changes its meaning.

**Assessment:** This is a valuable exception to plain-language substitution, especially for statistical names and
library types. Its behavior is already largely covered by S9 and the concrete definition rule in S37. The relevant
failure is lost precision, not the mere presence of a long or unfamiliar word.

**Related:** S37 explains necessary unfamiliar terms, S39 preserves literals, and the McNemar and exact-identifier
controls protect these cases.

**Recommendation:** Keep this exception in the single terminology paragraph. Pair it with a concrete referent instead of
repeating another preservation rule elsewhere.

**Principles:** Exception placement; density.

## S13: Keep and define materiality

> Shortening must not remove a material fact or relationship.

**Assessment:** This is a high-value invariant under strict word budgets. 'Material' is undefined, however, and can be
read as preserving every source detail. The useful criterion is whether omission changes the answer, its condition, its
confidence, or the next decision.

**Related:** S3 and S28 identify decision-changing information. The TL;DR evaluation protects counts and a
safety-threshold condition; the injected budget policy already forbids deleting a fact merely to meet a limit.

**Recommendation:** Preserve facts and relationships needed for the requested decision, including units, bounds,
conditions, and uncertainty. Do not turn fidelity into exhaustive copying.

**Principles:** Information preservation; proportionality.

## S14: Keep

> Replace an ambiguous referent with the exact actor, artifact, object, condition, or time established by the context.

**Assessment:** This names a concrete transformation and concrete referent classes. It is more operational than simply
asking for clarity and is backed by a pronoun-resolution evaluation. It should replace ambiguity, not eliminate every
pronoun after the actor and object are already unambiguous.

**Related:** S30 restates naming the same referents in recovery; S37 uses the same technique for unfamiliar terms. S1
determines which referents matter.

**Recommendation:** Keep as the canonical referent-resolution instruction; have recovery point here rather than
duplicate the whole inventory.

**Principles:** Observable behavior; single ownership.

## S15: Keep

> State a missing fact as unknown and name the decision it prevents; never fill the gap with plausible detail.

**Assessment:** The instruction to expose an unknown and the decision it blocks is specific and useful. It prevents
plausible detail from being presented as evidence. It should not imply that every uncertainty blocks a decision or that
the agent must stop instead of proceeding on a supported narrow interpretation.

**Related:** S28 repeats missing-evidence limits, S34 governs consequential clarification, and Core Evidence and
Autonomy own factual verification and whether to ask.

**Recommendation:** Keep the communication duty here: label the unknown and its practical consequence. Leave the
investigation and stopping threshold with their existing owners.

**Principles:** Evidence ownership; named failure.
