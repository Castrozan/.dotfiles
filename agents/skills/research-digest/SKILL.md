---
name: research-digest
description: On-demand research digest for any topic passed at invoke time; fans out across GitHub, arXiv, HN, Reddit, Lobste.rs and X, then dedups and ranks into a themed pulse. Use for "research digest", "catch me up on <topic>", or a curated AI/dev community pulse.
---

<invocation>
Extract the topic verbatim from the user request; it is always dynamic, never hardcoded. Run the bundled Claude JS Workflow at `<skill-base-dir>/research-digest.workflow.js` via `Workflow({ scriptPath, args: { topic, accounts, maxItems } })`. It returns `{ topic, digest, itemCount, sourcesHit }`. Relay `digest` to the user; on Discord post it through the reply tool. If the user named no topic, ask once or fall back to the workflow default.
</invocation>

<seed_accounts>
`seed-accounts.json` in this skill's base dir holds high-signal X handles. Read it and pass its `accounts` array as a soft signal boost only. The trap: the workflow must rank by topic relevance and include the best posts from any author; restricting results to the seed handles defeats the point. Edit that file to curate seeds; the topic itself stays caller-supplied.
</seed_accounts>

<failure_surfacing>
When `sourcesHit` is low or `itemCount` is 0, state it and name the source that failed (commonly `twikit-cli` auth for the X source) instead of presenting a thin digest as complete.
</failure_surfacing>

<boundaries>
Invoke-and-exit only: never daemonize, schedule, or stand up a service from this skill. A recurring run is a separate `schedule` routine that calls this skill and still exits each time. Every source is a free public API; stay within free tiers and add no paid search unless asked.
</boundaries>
