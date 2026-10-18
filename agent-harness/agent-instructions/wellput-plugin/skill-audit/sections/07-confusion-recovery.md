# Confusion recovery: sentence audit

Sentence IDs S29-S34. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#confusion-recovery).

## Section assessment

Retain a dedicated recovery behavior because the evaluation suite encodes specific past failures, including opaque
terms, missing referents, and unanswered decisions. Inspection is different from presuming that anger proves a language
failure. The actionable repair is to answer the unresolved question and show the missing relationship; a stance of
failure and an undefined change of abstraction level are weaker guidance.

Most useful content: the behaviors behind S30-S31, grounded by the existing controls. Main repair: merge
superficial-wording warnings and operationalize the recovery step. See F06 and F07.

## S29: Make the response observable

> When the reader signals confusion, treat the preceding explanation as failed.

**Assessment:** The trigger is appropriate, but 'treat ... as failed' describes an internal stance rather than the
corrective act. It also does not distinguish an explanation that was factually wrong from one that did not answer the
reader's question. Explicitly acknowledging failure is not required by the existing outcome-first rubric.

**Related:** S6 requests inspection without presuming a language failure. S30 contains the actual recovery action; the
operational-anger control prevents overdiagnosis.

**Recommendation:** When the reader signals confusion, identify the unanswered question or unresolved relationship and
replace the explanation accordingly.

**Principles:** Observable action; trigger precision.

## S30: Replace vague abstraction advice

> Restart one abstraction level below that answer: state the exact answer first; name each actor, artifact, referent,
> and relationship; then add only the mechanism needed to support the answer.

**Assessment:** 'One abstraction level below' has no shared scale and can produce extra implementation detail when the
user actually needs the result or decision. Naming actors and relationships is useful, but requiring every listed
element in every recovery can cause another report-shaped answer.

**Related:** S1, S14, and S27 already supply the answer, referents, and action. The user-visible-outcome and
small-question evaluations provide the intended behavioral boundary.

**Recommendation:** Answer the unresolved question first, name the missing referents or dependencies, and explain only
the mechanism needed to connect them.

**Principles:** Clarity; bounded repair; single ownership.

## S31: Merge with terminology recovery

> Use the reader's established terms and do not reuse a term the reader has rejected.

**Assessment:** Respecting the reader's established vocabulary is valuable and a rejected term is a concrete failure
signal. The rule needs the fidelity exception: a rejected word may still be an exact API identifier or a necessary
scientific term that must be preserved and explained.

**Related:** S10 owns established vocabulary, S12 protects precision, S37 defines necessary terms, and S39 protects
literals. The exact-identifier control is a counterexample to deleting all unfamiliar names.

**Recommendation:** Keep the rejection cue in recovery, but point to the single terminology rule and preserve exact
technical names when the task requires them.

**Principles:** Exception placement; source fidelity.

## S32: Replace with one observable repair

> Replacing invented or unfamiliar terms with the context's established terms is recovery; vocabulary substitution
> that leaves actors, referents, relationships, or behavior undefined is not.

**Assessment:** The first clause equates replacing unfamiliar terms with recovery, while the second correctly says that
vocabulary substitution can leave the failure intact. That tension makes the sentence look more decisive than it is. Its
useful lesson is that changing labels must also expose the underlying actor and relationship.

**Related:** S14 and S30 provide the operational repair; S33 repeats the insufficiency of reformatting; S62 repeats the
limit of word substitution.

**Recommendation:** State one positive action: restore the missing actor, action, or dependency before choosing clearer
wording.

**Principles:** Internal clarity; density; observable repair.

## S33: Merge, preserving the failure

> Moving the same undefined concepts into a table, replacing them with childish metaphors, or adding new labels
> preserves the failure.

**Assessment:** The warning is grounded in the existing table-with-undefined-concepts evaluation, so it is not generic
caution. It repeats S32's lesson and adds a subjective insult, 'childish', that does not help distinguish a valid
analogy from a replacement for missing facts.

**Related:** S19 addresses prose tables, S21 judges visual usefulness, and S30 specifies what the explanation must
recover.

**Recommendation:** Keep the concrete failure once: a different representation or metaphor does not repair unnamed
actors and relationships.

**Principles:** Named failure; tone precision; density.

## S34: Keep the boundary, narrow the dependency

> Ask only when a missing referent would materially change the answer under core
> `[autonomy](references/core.md#autonomy)`; otherwise state the narrow supported interpretation and continue.

**Assessment:** This correctly avoids asking about a missing fact that cannot change the answer, but it duplicates the
broader Autonomy owner and imports that policy into the portable package. 'Missing referent' can also be too narrow: a
missing threshold or scope may change the answer without being a pronoun-resolution problem.

**Related:** S15 names unknowns, S1 establishes the decision, and exported Core Autonomy governs the action threshold.
S25 exposes the same dependency issue.

**Recommendation:** For writing, state the supported interpretation when ambiguity does not change the answer; ask when
the missing information changes the requested decision or meaning.

**Principles:** Scope ownership; actionable uncertainty.
