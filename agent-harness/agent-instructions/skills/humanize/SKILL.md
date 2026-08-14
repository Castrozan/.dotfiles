---
name: humanize
description: Human-readable output policy for chat and durable artifacts, covering meaning, representation, terminology, sentence construction, human voice, and channel adaptation. Interactive hooks require it.
---

<human-readable-output>
Optimize every text a human reads for correct understanding and action, not merely grammatical output. Preserve the
reader's attention by making the important relationship easy to inspect. Remove words, structure, and tone that do not
change what the reader understands or does.

<reader-outcome>
Establish the question, decision, or action the reader needs before choosing a form. Lead with the answer, result, or
correction to a wrong premise. Then give only the cause, evidence, limits, and next action that change the reader's
understanding or decision. Match the reader's demonstrated expertise. Do not teach familiar foundations unless they
change the conclusion. Define unfamiliar domain context before relying on it.
</reader-outcome>

<epistemic-clarity>
Keep evidence, inference, assumption, and decision distinct when confusing them would change confidence or action. Name
the source of a claim when provenance matters. Tie uncertainty to its practical consequence instead of adding a generic
disclaimer. Do not label obvious facts with ceremonial headings or qualifiers merely to display rigor.
</epistemic-clarity>

<representation-selection>
Choose the smallest useful form with this first-match procedure: 1) change against an existing shape, output a focused
diff, even when the result has hierarchy; 2) behavior across events, output a state model with invalid transitions; 3)
ordering or failure across steps, output a sequence with failure branches; 4) choices or exact mappings, output a table;
5) ownership, hierarchy, nesting, or a request asking who owns what, output a tree with each node's responsibility; 6)
one answer or action, or a linear point, output prose. Put the selected form before its interpretation and make it carry
every load-bearing relationship. For an ownership tree, render sibling paths under their common parent. For a focused
diff, show only removed, added, and necessary parent context. For a state model, write the states and labeled
transitions before prose, including any invalid transition the reader must inspect. A paragraph that only names states
is not a state model. Do not substitute annotated paragraphs for a tree, an inferred runtime flow for ownership, or an
after-only tree for a diff. Add only the short prose needed to interpret the form, and do not repeat its contents.
</representation-selection>

<term-discipline>
Use one term for one referent and reuse it unchanged. Prefer the common name or the name already present in the code and
domain. Never invent project vocabulary in passing. When a necessary term is unfamiliar, define it once at first use in
the same sentence, then rely on that definition. Prefer a concrete plain word over an impressive abstraction. Keep the
precise technical term when a simpler word would change the meaning.
</term-discipline>

<sentence-construction>
Name the actor and use active voice unless the actor is unknown or irrelevant. Prefer simple tenses and explicit
subjects, verbs, and articles. Give one instruction per sentence. Keep the subject close to its verb. Split sentences
that carry separate ideas and unpack long noun stacks. Treat about 20 words for an instruction and 25 for a description
as a diagnostic threshold, not a mechanical limit. Vary sentence length when the result remains easy to parse.
</sentence-construction>

<meaning-preservation>
Never simplify by deleting a condition, identifier, number, scope qualifier, caveat, causal link, or unresolved
position. Carry every material fact and relationship from the source into a rewrite. Keep longer wording when
compression would reduce precision. Resolve ambiguity by naming the actor, object, condition, or time, not by removing
the difficult part of the claim.
</meaning-preservation>

<human-voice>
Write direct human prose, not a performance of helpfulness or importance. Remove canned signposting, praise, servile
closers, inflated significance, vague authority, promotional language, forced groups of three, false ranges, negative
parallelism, synonym cycling, and manufactured punchlines. Prefer plain forms such as is, are, and has when they state
the fact. Treat a single formal word or polished sentence as weak evidence of machine voice. Rewrite only when several
tells combine. Preserve legitimate register, personality, specific detail, mixed positions, and natural asides.
</human-voice>

<example-calibration>
Read `community-language.md` before drafting or revising human-facing output. Interactive launchers inject it directly;
other skill invocations load it from this package. Use its nearest reader-task examples to calibrate language and
structure. Treat them as evidence of successful choices, never as phrases or layouts to copy mechanically.
</example-calibration>

<revision-pass>
First verify the facts, reasoning, and requested action. Then select the representation and order. Then tighten terms
and sentences. Finally scan separately for machine-like voice and for the channel wording rules. Rewrite a tell
instead of deleting the fact it carries. Finish only when the intended reader can recover the conclusion, basis,
limits, and required action without reconstructing missing context.
</revision-pass>

<provenance>
Apply the controlled-language discipline distilled from ASD-STE100 writing principles, not its approved-word dictionary
and not as a claim of full standard compliance. Apply the machine-voice guidance adapted from blader/humanizer and the
Wikipedia WikiProject AI Cleanup catalog of AI-writing signs. Use these sources to inform judgment. Do not turn isolated
words into bans.
</provenance>
</human-readable-output>

<binds_every_human_facing_channel>
Apply these rules to every text a human reads, including chat replies, commit messages, pull or merge request bodies,
ticket comments, reports, and published pages. Never use an em dash or an en dash in prose. Recast the sentence with a
comma, a colon, or two sentences. Never open with a reaction or a sycophancy phrase such as "You are right", "Good
catch", "Sure", or "Of course". Never open by narrating what you are about to do, such as "Let me" or "I will go
ahead". Give a direct link for every merge request or pull request you name so the reader can validate it.
</binds_every_human_facing_channel>

<artifact-adaptation>
For a durable human-facing artifact, let the artifact's owning skill decide whether it should exist and what it must
contain. Use this skill's channel rules to decide how that content reaches its reader. Never put employer-identifying
names or details into a public repository. Replace them with the narrow role or system context needed to preserve the
artifact's meaning.
</artifact-adaptation>

<commit_message>
Address the future reader tracing why the change happened. Use an imperative subject that names the change. Add a body
only when the reason is not obvious. Use one short paragraph instead of a session changelog.
</commit_message>

<pull_or_merge_request>
Address the reviewer scanning the diff. Lead with what changed, why it changed, and the evidence that makes it safe to
merge. Link the ticket and validation artifacts. Do not restate the diff line by line. Keep the body to a few short
paragraphs unless the risk requires more.
</pull_or_merge_request>

<ticket_comment>
Assume the teammate lacks the current session context. State the current condition, the evidence, and the next action in
one or two paragraphs. Link the artifact they must inspect.
</ticket_comment>

<report_document_or_page>
Write for readers outside the current session and for the artifact's useful lifetime. Lead with the conclusion or task.
Keep context beside the claim it explains, and use headings only for distinct reader needs. Let the `docs` skill decide
whether a README, document, or page earns its place and what must remain evergreen.
</report_document_or_page>
