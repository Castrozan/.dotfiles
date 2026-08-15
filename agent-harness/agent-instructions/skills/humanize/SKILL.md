---
name: humanize
description: Human-readable output policy for chat and durable artifacts. It routes substantial writing through a controlled-language rulebook, selects the smallest useful representation, and adapts the result to its human-facing channel. Interactive hooks route failed replies to it.
---

<humanize-routing>
Use this skill for substantial text that a human must understand or act on. The skill that owns the work establishes the
facts, technical decision, artifact type, and channel-specific requirements. Humanize governs how that information
reaches the reader.

<controlled-language-loading>
Read `community-language.md` completely before drafting or revising a substantial explanation, diagnosis, decision,
warning, report, summary, or durable human-facing artifact. It is the normative policy for meaning, certainty,
terminology, noun groups, verbs, sentences, procedures, descriptions, warnings, context, and human voice. It contains
rules, not an example corpus. Apply it as a whole rather than selecting only the sections that confirm the first draft.

A one-sentence or two-sentence confirmation or factual answer does not require the rulebook. When an interactive Stop
hook routes a failed reply to this skill, load the rulebook before retrying. Exact source facts and the owning skill's
technical or artifact requirements take precedence over stylistic compression.
</controlled-language-loading>

<representation-selection>
Choose the smallest useful form with this first-match procedure:

1. For change against an existing shape, use a focused diff, even when the result has hierarchy.
2. For behavior across events, use a state model with the invalid transitions the reader must inspect.
3. For ordering or failure across steps, use a sequence with the material failure branches.
4. For choices or exact mappings, use a table.
5. For ownership, hierarchy, or nesting, use a tree with each node's responsibility.
6. For one answer, one action, or a linear point, use prose.

Put the selected form before its interpretation and make it carry every load-bearing relationship. Render sibling paths
in an ownership tree under their common parent. In a focused diff, show only removed, added, and necessary parent
context. In a state model, write states and labeled transitions before prose. A paragraph that names states is not a
state model. Do not substitute annotated paragraphs for a tree, an inferred runtime flow for ownership, or an
after-only tree for a diff.

Add only the prose needed to interpret the form. Do not repeat its contents. Preserve a before-and-after contrast when
the reader needs to inspect how the same system changed. Put a measurement beside the stage that produced it and label
the artifact handed across a boundary.
</representation-selection>

<binds-every-human-facing-channel>
Apply the controlled-language rulebook to every text a human reads, including chat replies, commit messages, pull or
merge request bodies, ticket comments, reports, and published pages. Let the skill that owns the artifact define its
required content and structure.

Never use an em dash or an en dash in prose. Recast the sentence with a comma, colon, or two sentences. Never open with
a reaction or sycophancy phrase such as "You are right", "Good catch", "Sure", or "Of course". Never open by narrating
what you are about to do, such as "Let me" or "I will go ahead". Give a direct link for every merge request or pull
request you name so the reader can validate it.
</binds-every-human-facing-channel>

<report-document-or-page>
Write for readers outside the current session and for the artifact's useful lifetime. Lead with the conclusion or task.
Keep context beside the claim it explains, and use headings only for distinct reader needs. Let the `docs` skill decide
whether a README, document, or page earns its place and what must remain evergreen.
</report-document-or-page>
</humanize-routing>
