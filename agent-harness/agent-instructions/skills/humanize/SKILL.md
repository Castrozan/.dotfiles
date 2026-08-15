---
name: humanize
description: Human-readable output for chat and durable artifacts. Routes substantial writing through controlled-language rules, selects the smallest useful representation, and adapts it to its channel.
---

<controlled-language-loading>
Read `community-language.md` completely before drafting or revising a substantial explanation, diagnosis, decision,
warning, report, summary, or durable human-facing artifact. Apply it as one policy. Skip it only for a one-sentence or
two-sentence confirmation or factual answer. Load it before retrying a reply routed here by an interactive Stop hook.
Preserve exact source facts and the owning skill's technical or artifact requirements when stylistic compression
conflicts with them.
</controlled-language-loading>

<representation-selection>
Choose the smallest useful form with this first-match procedure: 1) for change against an existing shape, use a focused
diff, even when the result has hierarchy; 2) for behavior across events, use a state model with material invalid
transitions; 3) for ordering or failure across steps, use a sequence with material failure branches; 4) for choices or
exact mappings, use a table; 5) for ownership, hierarchy, or nesting, use a tree with each node's responsibility; 6) for
one answer or action, or a linear point, use prose. Put the selected form before its interpretation and make it carry
every load-bearing relationship.
</representation-selection>

<representation-rendering>
Render sibling ownership paths under their common parent. Show only removed, added, and necessary parent context in a
focused diff. Write states and labeled transitions before prose in a state model; a paragraph that names states is not
a state model. Preserve a before-and-after contrast when the reader must inspect how the same system changed. Put each
measurement beside the stage that produced it and label artifacts handed across boundaries. Add only the prose needed
to interpret the form, and never repeat relationships the form already shows.
</representation-rendering>

<human-facing-channel-rules>
Apply the controlled-language policy to every text a human reads. Let the skill that owns the artifact define its
required content and structure. Never use an em dash or en dash in prose; use a comma, colon, or two sentences. Never
open with a reaction or sycophancy phrase such as "You are right", "Good catch", "Sure", or "Of course". Never open by
narrating the intended action with phrases such as "Let me" or "I will go ahead". Give a direct link for every merge
request or pull request named in the text.
</human-facing-channel-rules>

<durable-report-rules>
Write reports, documents, and pages for readers outside the current session and for the artifact's useful lifetime.
Lead with the conclusion or task, keep context beside the claim it explains, and use headings only for distinct reader
needs. Let the `docs` skill decide whether the artifact earns its place and what must remain evergreen.
</durable-report-rules>
