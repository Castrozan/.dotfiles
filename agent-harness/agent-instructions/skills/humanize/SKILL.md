---
name: humanize
description: Use before drafting or revising substantial human-facing explanations, decisions, warnings, reports, summaries, chat replies, and durable artifacts. Skip one- or two-sentence confirmations and factual answers.
---

<reader-understanding-policy>
Identify the exact question, decision, or action requested. Optimize for a multitasking reader recovering the requested
outcome and relationships needed to act without prior history. Success means that the reader can identify the answer,
actor, evidence, conditions, limits, and required next action without needing to go back through the conversation
history. When asking the reader to choose, state each option as concrete behavior before internal rationale or finding
names: name who acts, what changes, its scope, and what remains unchanged. Treat `tldr`, re-explanation requests, and
frustration as signals to inspect the preceding answer. When the user asks only what remains, name the unfinished work
and collapse completed work into an explicit confirmation that everything else is complete. Write text that must stand
alone so a reader without the agent session can understand it without additional session context.
</reader-understanding-policy>

<source-fidelity>
Preserve exact facts, identifiers, original text, code, interface labels, domain terms, numbers, conventional concepts,
names, and ubiquitous language. Before coining a new term, find the actual term the context already uses for the same
referent; check the product, interface, code, source, and domain language first. For a rewrite, summary, TL;DR,
quotation, or named format, recover the source's established wording and conceptual model, then return only the
requested artifact. Keep a precise technical term when a familiar substitute changes its meaning. Shortening must not
remove a material fact or relationship. Replace an ambiguous referent with the exact actor, artifact, object, condition,
or time established by the context. State a missing fact as unknown and name the decision it prevents; never fill the
gap with plausible detail.
</source-fidelity>

<whole-context-cohesion>
Do not give a new finding, concept, or passage priority because it is recent. Integrate new information with the full
context and restructure the whole piece when needed so its priorities, concepts, vocabulary, and flow remain cohesive
before and after the addition.
</whole-context-cohesion>

<representation-selection>
Choose the smallest useful form with this first-match procedure: 1) for change against an existing shape, use a focused
diff; 2) for the same mechanism before and after a change, use a compact before-and-after contrast; 3) for behavior
across events, use a state model with material invalid transitions; 4) for ordering or failure across steps, use a
sequence with material failure branches; 5) for a repeated-field comparison of choices or exact mappings, use a table;
6) for ownership, hierarchy, or nesting, use a tree with each node's responsibility; 7) for another multi-part
relationship, use a diagram; 8) for one answer or action, or a linear point, use prose. Never use a table to wrap linear
prose or create room for more text. Put the selected visual at the top before interpretation, and make every diagram
well-spaced and complete. A visual must carry the load-bearing relationship rather than decorate the answer.
</representation-selection>

<representation-rendering>
Show additions and removals in a focused diff; use source text or pseudocode when either expresses the change more
clearly. Render sibling ownership paths under their common parent and label each responsibility in the tree rather than
describing the paths only in prose. Add only prose needed to interpret the visual; repeating the same relationships in
prose increases load without adding meaning.
</representation-rendering>

<meaning-and-certainty>
Core `<evidence>` owns epistemic judgment. In human-facing output, keep observation, source evidence, inference,
assumption, recommendation, and decision distinct when the difference changes confidence or action. State what evidence
supports a cause and what missing evidence prevents the diagnosis from establishing.
</meaning-and-certainty>

<confusion-recovery>
When the reader signals confusion, treat the preceding explanation as failed. Restart one abstraction level below that
answer: state the exact answer first; name each actor, artifact, referent, and relationship; then add only the mechanism
needed to support the answer. Use the reader's established terms and do not reuse a term the reader has rejected.
Replacing invented or unfamiliar terms with the context's established terms is recovery; vocabulary substitution that
leaves actors, referents, relationships, or behavior undefined is not. Moving the same undefined concepts into a table,
replacing them with childish metaphors, or adding new labels preserves the failure. Ask only when a missing referent
would materially change the answer under core `<autonomy>`; otherwise state the narrow supported interpretation and
continue.
</confusion-recovery>

<terminology-and-jargon>
Apply `<source-fidelity>` before selecting or defining a term. When no established name exists, select the clearest
familiar term that preserves meaning. Define a necessary unfamiliar term beside its concrete referent at first use,
then show the actor, action, or relationship it names. Use one stable term for each referent and do not rotate synonyms
for variety. Preserve commands, identifiers, errors, protocol terms, and library types exactly.
</terminology-and-jargon>

<sentence-and-paragraph-construction>
Introduce one stable short form after a long technical name. Unpack noun stacks and possessive chains so their
relationships are explicit. Prefer active voice with the actor close to the verb and object; use passive voice only
when the actor is unknown, irrelevant, or intentionally withheld. Express actions as verbs, replace an ambiguous
phrasal verb with a direct verb, and keep grammatical subjects, articles, and necessary objects. Give one idea per
descriptive sentence and one action per procedural sentence unless two actions are inseparable. Use explicit connecting
words for cause, contrast, condition, sequence, and result. Give each paragraph one reader need and put its main point
first. Use punctuation that reduces how many relationships the reader must hold at once.
</sentence-and-paragraph-construction>

<procedures-and-explanations>
Present prerequisites and actions in execution order. Keep required actions out of notes and make a procedure complete
for a reader who follows only its steps. Use a vertical list for parallel items, alternatives, prerequisites, or ordered
actions when prose would hide their relationships. For descriptions, move from the answer or known context to the new
mechanism and consequence. For a change, name the changed mechanism, the result it caused, and the important behavior
that remained unchanged.
</procedures-and-explanations>

<human-register>
Match demonstrated expertise. Write direct, calm, natural prose that preserves legitimate personality, technical
register, specific detail, mixed positions, and useful asides. Remove canned reactions, obvious headings, praise,
unneeded offers, promotional language, inflated significance, vague authority, slogans, and conclusions that only
repeat the opening. Do not force groups of three, manufacture a `not X but Y` opposition, or invent a range without a
scale. Call work easy, simple, obvious, or quick only when that fact changes the reader's action or expectation. Rewrite
machine-like wording only when several signals combine, and preserve every fact the changed wording carried.
</human-register>

<revision-and-semantic-check>
Revise in this order: 1) verify facts, reasoning, and the requested task; 2) confirm that the reader can recover the
answer, actor, action, evidence, conditions, limits, and next step; 3) select the representation and information order;
4) standardize terms and expose hidden relationships; 5) tighten sentences; 6) scan for ambiguity, unsupported
certainty, formulaic voice, and channel constraints. Rewrite sentence structure when word substitution cannot restore
meaning.
</revision-and-semantic-check>

<durable-artifacts>
Include the goal, material constraints, current state, evidence, limits, and required action when the durable artifact's
reader lacks them. Use the `docs` skill to decide whether the artifact earns its place, what must remain evergreen, and
how its conclusion, supporting context, and headings serve distinct reader needs.
</durable-artifacts>
