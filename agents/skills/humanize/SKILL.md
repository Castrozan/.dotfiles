---
name: humanize
description: De-slop human-facing prose: strip AI-writing tells and phrase per channel (commit, MR, ticket, doc, chat). Use when writing or editing text a human reads.
---

<axis>
core.md audience routed you here because the reader is a human, so the job is voice and phrasing, not whether to constrain. This skill carries the de-slop pattern library core.md does not; the em-dash and no-employer-names rules in core.md user still bind every channel.
</axis>

<scan_as_a_separate_pass>
De-slop is its own editing pass, not folded into tightening or restructuring: the tells are lexical and tonal habits that survive any trimming, so scan for them explicitly. Humanize by rewriting, never by deleting; the rewrite covers every point the original carried, because removing a tell must not strip the fact it wrapped. Fix the substance first, then the voice.
</scan_as_a_separate_pass>

<tell_catalog>
For the pattern families, read `tells.md`: the AI vocabulary cluster, inflated significance, copula avoidance and grammar tells, chat and sycophancy artifacts, the em-dash and punctuation check, the register gate, and the combinatorial false-positive guard that keeps you from flattening real human prose over one isolated marker.
</tell_catalog>

<per_channel>
For phrasing each surface a human reads (commit message, PR or MR description, ticket comment, published page, live keyboard reply), read `channels.md`.
</per_channel>

<provenance>
Adapted from blader/humanizer (MIT, https://github.com/blader/humanizer, pulled at v2.8.0) operationalizing Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup). Distilled into this repo's dense form, not synced verbatim, so it ages by deliberate re-pull, a diff against v2.8.0, not silent drift. Re-pull when the model-era vocabulary cluster has visibly moved.
</provenance>
