# Terminology and jargon: sentence audit

Sentence IDs S35-S39. [Audit overview](../../skill-audit.md). [Full sentence review](../../skill-review.md#terminology-and-jargon).

## Section assessment

The distinct useful operations are introducing a necessary unfamiliar term with its referent and maintaining a stable
term thereafter. The section otherwise repeats source fidelity and redirects to it. Folding these operations into one
terminology owner would preserve their behavior while reducing the number of parallel commands that can drift. An
empirical ablation is still needed before claiming that consolidation improves model output.

Most useful content: S36-S38. Main repair: preserve these operations while merging the redundant pointer and
literal-preservation command into fidelity. See F04 and F06.

## S35: Delete the redundant pointer or merge

> Apply `[source fidelity](#source-fidelity)` before selecting or defining a term.

**Assessment:** This only redirects to the immediately relevant source-fidelity policy and adds no trigger, exception,
or observable behavior. Its term-selection operation is already specified in S10 and its own following sentences.
Removing this line is a static consolidation candidate, not a measured guarantee of unchanged model behavior.

**Related:** S10 is the stronger canonical rule. S36-S39 can sit beside it without a separate forwarding sentence.

**Recommendation:** Consolidate terminology into the fidelity section and retain one owner rather than this redundant
preamble.

**Principles:** Density; canonical ownership.

## S36: Keep as an exception

> When no established name exists, select the clearest familiar term that preserves meaning.

**Assessment:** This gives the useful fallback when the existing domain supplies no name. 'Familiar' must be judged for
the actual reader, and a new identifier may be dictated by the user's task or a code interface rather than chosen for
rhetorical simplicity.

**Related:** S10 requires checking established vocabulary first; S37 handles an unavoidable unfamiliar term; S55
calibrates reader expertise.

**Recommendation:** Keep next to S10 with the no-established-term condition and the requirement to preserve the intended
meaning.

**Principles:** Exception placement; audience fit.

## S37: Keep

> Define a necessary unfamiliar term beside its concrete referent at first use, then show the actor, action, or
> relationship it names.

**Assessment:** The rule joins an unfamiliar term to a concrete referent and then the relevant relationship. That is
more helpful than either replacing all jargon or merely appending a dictionary definition. It can still be shortened by
avoiding the repeated actor/action/relationship inventory when the surrounding sentence already makes those roles clear.

**Related:** S12 protects precision, S14 resolves referents, S30 uses the same technique for recovery, and the McNemar
control tests a legitimate technical name.

**Recommendation:** Keep in the single terminology owner. Define only the unfamiliar part needed for the current
explanation.

**Principles:** Observable behavior; proportionality.

## S38: Keep and colocate

> Use one stable term for each referent and do not rotate synonyms for variety.

**Assessment:** Stable terminology is a concrete way to prevent one entity appearing to be several. It does not require
repeating a long name in every sentence; an unambiguous pronoun or a genuinely different role is not a synonym rotated
for variety.

**Related:** S9 preserves identity, S10 establishes the canonical term, S14 only replaces ambiguous pronouns, and S40
introduces a short form.

**Recommendation:** Keep beside term selection. Apply consistency to referents while retaining ordinary unambiguous
reference.

**Principles:** Consistency; exception clarity.

## S39: Merge and scope

> Preserve commands, identifiers, errors, protocol terms, and library types exactly.

**Assessment:** This repeats part of S9 almost exactly. It is an important control against 'simplifying' an API name or
a library type into an inaccurate term, but exact preservation should apply while reporting or quoting, not forbid a
requested rename or code change.

**Related:** S9 owns exactness, S11 defines transformation scope, and the exact-identifier evaluation protects all three
named code entities.

**Recommendation:** Retain the technical-literal examples in the canonical fidelity rule and remove the second
independent command.

**Principles:** Density; task scope.
