<framing>
Every channel below is human-facing, so the core.md audience rule applies first: lead with the answer and cut filler. These notes add only what shifts per channel, the reader and what they do next.
</framing>

<commit_message>
A commit message addresses a future reader tracing why a change happened, not the operator who watched it. Imperative subject naming what changed; a body only when the why is non-obvious; no narration of the work session. This is a public repo, so no employer-identifying names.
</commit_message>

<pull_or_merge_request>
A PR or MR description addresses a reviewer scanning a diff. Lead with what changed and why it is safe to merge, link the ticket, and do not recap the diff line by line; the diff is already in front of them.
</pull_or_merge_request>

<ticket_comment>
A ticket comment addresses a teammate who lacks your session context. State the current state and the next action plainly, and link the artifact (MR, PR, build, page) so they click through instead of reconstructing it.
</ticket_comment>

<published_page>
A published page or any public-repo text reaches an audience you do not control, indefinitely. Exclude employer-identifying names and private detail, and write so it still reads coherently long after the change that produced it.
</published_page>

<live_keyboard_reply>
A live keyboard reply defers entirely to interactive-preferences.md for shape, the Done and Next labels, no lists, the Stop hook. This skill supplies the de-slop library underneath that shape, not the reply mechanics.
</live_keyboard_reply>
