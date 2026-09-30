# Arena.ai on Claude Opus 5.5 writing measures

Capture: `ReadItLater Inbox/Tweet from Arena.ai (2026-09-25 19-13-06).md`
Origin: https://x.com/arena/status/2103532528946839901
Verdict: **drop**

## The origin as resolved

Read through the twitter skill from the capture's own first link. `twikit-cli tweet 2103532528946839901`
resolved the post to Arena.ai (@arena), published 2026-09-25 at 17:10:11 UTC. `twikit-cli thread` found no
self-thread. At read time it reported 2,104 likes, 121 reposts, 96 replies, and 1,501,354 views.

The raw endpoint truncated the post, so the unattended browser workflow opened that same URL and exposed the complete
accessible text. Arena.ai says it compared Claude Opus 5.5 with Opus 5 on unspecified high-reasoning Text Arena
outputs and that 10 of 12 writing measures moved in a better direction. The disclosed comparisons are:

- long content words: 41.7% to 38.6%;
- mean sentence length: 12.14 to 10.03 words, a 17% reduction;
- mean answer length: 453 to 481 words, a 6% increase;
- em dashes: 95% fewer;
- semicolons: 73% fewer;
- hedges and caveats such as `perhaps` and `arguably`: 0.39 to 0.77 per 1,000 words, a 97% increase.

The post calls shorter sentences and fewer long words easier to read, calls the longer answers a tradeoff, and presents
the punctuation changes as less recognizably AI. It suggests that the increased hedge rate may be a new AI giveaway.
It does not give a sample size, sampling procedure, rubric definitions beyond the examples, significance estimates,
the underlying outputs, or a link to a methods report.

## What it actually is

A model-release style comparison, not a writing method and not a reproducible benchmark. It mixes descriptive measures
with value judgments: sentence length and punctuation frequency can be counted, but fewer semicolons is not inherently
better, and a caveat can be either empty verbal padding or the exact uncertainty a reader needs. The post does not
separate those cases.

The useful observation is narrow: a newer model can improve local readability measures while becoming wordier and more
hedged. The post does not establish a threshold that should become policy, a failing behavior in this repository, or a
repeatable evaluation that could tell whether a local change helped.

## What it touches here

It overlaps with the existing Humanize policy but requires no repository change:

- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:25-33` already preserves exact facts and necessary
  conditions while shortening.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:61-66` already requires evidence, inference,
  uncertainty, recommendation, and decision to remain distinct. A blanket hedge reduction would conflict with this
  when uncertainty is material.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:80-96` already selects familiar precise terms,
  gives one idea or action per sentence, and chooses punctuation by the relationships the reader must hold.
- `agent-harness/agent-instructions/skills/writing/humanize/SKILL.md:107-125` already removes formulaic voice and
  promotional inflation, tightens sentences, and checks unsupported certainty.
- `agent-harness/hooks/runtime/common/human_facing_reply/reply-formats.json:120-125` already rejects em and en dashes
  outside quotations. The local rule is deterministic and stronger than the post's observed 95% reduction.
- `agent-harness/quality/evaluations/evals/communication.yaml:79-116` already tests concise output without losing a
  material caveat and tests separation of evidence from an unverified diagnosis.
- `agent-harness/quality/evaluations/evals/communication.yaml:118-130` and `:162-173` already test removal of machine-like
  inflation and a direct recommendation when the supplied tradeoff decides it.

It replaces and deletes nothing. Adding bans or numeric ceilings for long words, semicolons, answer length, or hedge
tokens would replace contextual semantic checks with proxies that the source has not validated. Adding another
communication evaluation from the same desired behavior would duplicate coverage without a demonstrated gap.

## Reasoning

Drop, rather than adopt or trial. The strongest possible adoption is a new style-metric evaluation, but the post does
not disclose enough method or data to reproduce its measures, and this repository intentionally tests whether meaning,
uncertainty, and action survive a rewrite. Those criteria distinguish good concise writing from merely low counts. A
trial would have the same problem: without the Arena sample and definitions, a local count cannot reproduce the claim
or set a justified threshold.

Drop, rather than learn. There is no bounded practice named by the source beyond counting surface features, and the
repository already has both model-graded communication evaluations and deterministic punctuation checks. A useful study
would need the missing corpus and methodology, not repeated inspection of the six headline numbers.

Drop, rather than reference. The model-specific comparison is likely to age quickly, supplies no reproducible artifact,
and contributes no reusable rule beyond existing policy. Filing it would preserve a promotional snapshot whose only
durable lesson is already encoded more precisely in the repository: tighten prose without deleting evidence,
conditions, or warranted uncertainty.

## Drafted vault entry

None. A drop files no Second Brain entry. The capture and this decision retain the origin, disclosed measurements,
repository fit, and reason for discarding it without adding a low-evidence item to `Learning MOC`.
