<framing>
Every channel below is human-facing, so the same discipline runs first: build with `simplified-technical-english.md`,
strip with `tells.md`, obey `enforced-wording-rules.md`. Lead with the answer, the status, or the correction to a wrong
premise, so the text stands alone if the reader stops after the first sentence, then descend into cause and detail.
Cite code by `file_path:line_number` and link artifacts rather than pasting diffs, output, or file bodies past a few
load-bearing lines. This repo is public and these channels reach readers you do not control, so carry no
employer-identifying name on any of them. What follows is only what shifts per channel: the reader, what they do next,
and how much text they will tolerate.
</framing>

<commit_message>
A commit message addresses a future reader tracing why a change happened, not the operator who watched it. Imperative
subject naming what changed, then a body only when the why is non-obvious, and then one short paragraph rather than a
changelog of the session.
</commit_message>

<pull_or_merge_request>
A PR or MR description addresses a reviewer about to scan a diff. Lead with what changed and why it is safe to merge,
link the ticket, and do not recap the diff line by line, because the diff is already in front of them. A few short
paragraphs is the ceiling; past that the reviewer stops reading and opens the code.
</pull_or_merge_request>

<ticket_comment>
A ticket comment addresses a teammate who lacks your session context. State the current state and the next action
plainly in a paragraph or two, and link the artifact so they click through instead of reconstructing it.
</ticket_comment>

<published_page_or_document>
A published page, README, or doc reaches an audience you do not control, indefinitely, so write it to still read
coherently long after the change that produced it. Dense prose over bullet lists, no preamble announcing what the
document is about, and headings only where sections are genuinely distinct. Whether the document should exist at all,
and what belongs in it, is the `docs` skill's call, not this one's.
</published_page_or_document>

<live_keyboard_reply>
The live keyboard reply is the tightest channel and the only one whose template and limits are enforced rather than
chosen, so `enforced-wording-rules.md` and the reply template deployed with it govern; this chapter adds nothing there.
</live_keyboard_reply>
