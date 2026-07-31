---
name: humanize
description: The single home for how text a human reads is worded: plain-language discipline, AI-writing tells to strip, per-channel phrasing and length (chat, commit, MR, ticket, doc, page), and the wording rules a hook blocks on. Load before drafting any human-facing text.
---

<axis>
core.md routes here the moment the consumer is a human, so this skill decides how the words go and no other instruction
surface states a wording rule. Build the draft with the discipline in `simplified-technical-english.md`, then strip the
voice tells in `tells.md`. Fix the substance first, then the voice.
</axis>

<scan_as_a_separate_pass>
De-slop is its own editing pass, not folded into tightening or restructuring: the tells are lexical and tonal habits
that survive any trimming, so scan for them explicitly. Humanize by rewriting, never by deleting; the rewrite covers
every point the original carried, because removing a tell must not strip the fact it wrapped.
</scan_as_a_separate_pass>

<plain_language_discipline>
For word choice and sentence construction, read `simplified-technical-english.md`: one meaning per word, no project
vocabulary invented in passing, active voice, one instruction per sentence, and the rule that a rewrite never drops a
fact.
</plain_language_discipline>

<tell_catalog>
For the pattern families, read `tells.md`: the AI vocabulary cluster, inflated significance, copula avoidance and
grammar tells, chat and sycophancy artifacts, the punctuation check, the register gate, and the combinatorial
false-positive guard that keeps you from flattening real human prose over one isolated marker.
</tell_catalog>

<per_channel>
For phrasing each surface a human reads and the length each one carries, read `channels.md`.
</per_channel>

<machine_checked_rules>
For the wording rules a hook blocks on, read `enforced-wording-rules.md`. It is generated from the catalog the Stop
hook runs, and it binds every channel, not only the live keyboard reply where the check happens to execute.
</machine_checked_rules>

<provenance>
The tell catalog is adapted from blader/humanizer (MIT, https://github.com/blader/humanizer, pulled at v2.8.0)
operationalizing Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup). Distilled into this repo's dense form, not
synced verbatim, so it ages by deliberate re-pull, a diff against v2.8.0, not silent drift. Re-pull when the model-era
vocabulary cluster has visibly moved.
</provenance>
