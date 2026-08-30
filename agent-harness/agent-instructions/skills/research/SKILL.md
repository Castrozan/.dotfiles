---
name: research
description: Research current external information, comparisons, decisions, or themed digests. Use for latest facts, evaluation, verification, "catch me up", or community pulses; not local repository search.
---

<core_evidence_authority>
Core `<evidence>` owns consequential epistemic judgment and core `<autonomy>` owns the threshold for asking. This skill
owns the bounded source selection, currency, comparison, and citation procedure for external research.
</core_evidence_authority>

<research_intake>
Define the exact question before searching: what decision is being made, which options matter, what geography or
environment applies, and how current the answer must be. Convert broad asks into one of four shapes: current-state
answer, comparison, recommendation, or timeline. If one missing assumption blocks progress, ask once; otherwise state
the smallest useful assumptions and proceed.
</research_intake>

<source_strategy>
Prefer primary sources for factual claims: official documentation, vendor pages, maintainers, repositories, standards
bodies, papers, changelogs, and first-party announcements. Use secondary sources to validate adoption, pricing,
practitioner experience, or criticism. For unstable topics, favor recent sources and capture the exact publication or
effective date for every decisive source.
</source_strategy>

<research_workflow>
Start with 2-4 varied searches that attack different parts of the question: the direct topic, the likely alternatives,
recent updates, and one disconfirming angle. Expand only on results that can support a concrete claim. Stop when you
have enough evidence to answer the question, explain the main tradeoffs, and justify a recommendation without padding.
</research_workflow>

<evidence_handling>
Track each important claim with its supporting link, exact date, and whether it is sourced fact or your inference.
Verify high-stakes, fast-moving, surprising, or quantitative claims across multiple credible recent sources. When
sources disagree, surface the disagreement, explain which source is more authoritative, and keep the uncertainty visible
instead of flattening it.
</evidence_handling>

<decision_criteria>
Judge options on criteria that matter for the user's actual decision, not a generic checklist. Common criteria are fit,
maturity, maintenance, integration cost, security or compliance, pricing, and operational burden. Compare against the
user's current path when that baseline is known, because "better than the alternative" is usually the real question.
</decision_criteria>

<depth_selection>
Match depth to stakes. Use a short current-state answer for straightforward facts, a shortlist with tradeoffs for
spending or tooling choices, and a deeper comparison only when the decision is expensive, risky, or hard to reverse.
</depth_selection>

<answer_shape>
Lead with the answer, not the search log. Default output: TL;DR, decisive findings, recommendation, and sources. Use a
comparison matrix only when there are multiple serious options. Use absolute dates, cite exact links, separate sourced
facts from your synthesis, and say plainly when evidence is thin.
</answer_shape>

<validation>
Should trigger: "research X", "look into the latest Y", "compare A vs B", "evaluate whether we should use Z", "verify
the current state of W". Should not trigger: local repository code search, summarizing text the user already provided,
or purely internal documentation lookup. Functional check: take one realistic "latest" question and verify that the
answer contains dates, links, decisive tradeoffs, and a clear recommendation.
</validation>

<research_pulse>
For a research digest, community pulse, or "catch me up" request, collect recent topic-specific evidence across GitHub,
papers, practitioner discussion, and X. Extract the topic verbatim, read `research-pulse-seed-accounts.json`, and run
`research-pulse.workflow.js` through `Workflow` when its runner is available with `topic`, `accounts`, and `maxItems`.
Relay its digest and disclose low `sourcesHit` or empty `itemCount`; otherwise perform the same source sweep directly.
Treat the seed accounts as a relevance hint, never a source allowlist, deduplicate by underlying item, and rank by topic
fit instead of padding the result.
</research_pulse>
