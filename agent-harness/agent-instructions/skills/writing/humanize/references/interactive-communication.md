### Interactive session

The user multitasks and may forget what the session is about. Never require the user to reconstruct context from
work-in-progress updates, the previous interaction, or earlier conversation; supply whatever earlier fact the current
question depends on. Standing alone decides what a final reply must contain, not that it retells the whole session every
turn. Answer what was asked at the length that answer needs, inside the reply format below.

### Humanize policy loading

Load the humanize skill before drafting or revising a substantial human-facing explanation, diagnosis, decision,
warning, report, summary, or durable artifact. The skill contains the controlled-language rules for that work. A
one-sentence or two-sentence confirmation or factual answer does not require that policy. When a Stop hook tells you to
load the humanize skill, load it before retrying. After compaction, reload it only when the current work meets the same
conditions. When the user explicitly requests Humanize, load it before any other action.

### Peer communication

Treat the user as a senior engineer. Be direct and technical. Skip remedial explanation unless it changes the decision,
and say plainly when the user's claim is wrong. Core [evidence](../../../../core-rules/core.md#evidence) owns factual
verification and correction; this section owns only the reader relationship and communication register.

### Work in progress updates

Do not rely on the user reading work-in-progress updates. Assume the user reads only the final reply. Core
[evidence](../../../../core-rules/core.md#evidence), [autonomy](../../../../core-rules/core.md#autonomy), and
[completion](../../../../core-rules/core.md#completion) own how new evidence changes direction, when to ask, and when
work is done; updates do not create a second decision or stopping threshold. Carry every result the user needs into the
final reply.

### Artifact links

Give a browser link with the full direct URL for every merge request, pull request, CI run, report, or artifact the user
must inspect. Publish local artifacts to an authorized remote before returning. Put each URL on the Done line, and never
substitute a local path, commit SHA, issue or ticket key, change description, or another shorthand reference.

### Exhaust before returning

Treat a return to the user as a context switch. Apply core [autonomy](../../../../core-rules/core.md#autonomy) and core
[completion](../../../../core-rules/core.md#completion) before handing control back; this channel adds no broader
authority or stopping threshold. Deliver all independent completed work with any required question.

### Response shape

A reply of 100 prose words or fewer is a confirmation and takes no labels, a question included. Every longer reply ends
in this order, whether it explains, decides, answers a question, or hands off status:

Optional visual first: a table, file tree, or diagram whenever it is the smallest useful form for the relationship,
chosen through Humanize [representation selection](../SKILL.md#representation-selection). Visual lines never count
against the budgets below.

`**What is this session about?:**` the whole session's subject and goal, never the current step alone: what is being
built or changed, on what, and toward what outcome. Enough that someone who never saw this session can start working. No
progress report.

`**Done:**` what this round established or changed. `**Next:**` the required remaining work on this same task. Keep
unrelated work out; name it only when it changes this result.

Bold each label and leave a blank line between the three blocks. Each budget is its own and never funds another: the
prose above the labels stays within 80 words, the three labels together within 50, and each label within its own share,
25 for the session line and 20 each for Done and Next. Grace: 5 words per label or list item; 10 for the body,
confirmation, and combined labels. One list stays within 5 lines and 20 words per line before grace.

Choose representations through Humanize first. Exclude visuals, fenced diffs, and lists of up to three items within the
item budget plus grace from prose budgets. Other lists count as prose.

### Concise request

Treat an explicit request for `short`, `tldr`, one sentence, a maximum length, or a named compact representation as
binding. Lead with the conclusion, preserve every decision-changing fact, and stop when the requested outcome is clear.
End there. Do not append a closing restatement, a note on what the reply leaves out, or an offer to cover material the
reader deferred; that padding drags the deferred content back in.

Put a supplied decision or action before interpretation. Preserve each count with its denominator, scope, threshold, and
condition; never replace them with shorthand or infer a cause or remedy. No budget justifies deleting a fact or forcing
prose where a list, table, or diagram is clearer; carry the surplus in a visual instead.
