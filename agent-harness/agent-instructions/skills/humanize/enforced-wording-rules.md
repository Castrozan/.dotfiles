<generated_surface>
This file is generated from the reply rule catalog in `agent-harness/hooks/runtime/common/human_facing_reply`, the one
place these rules exist as prose, as regex, and as the reminder the hooks inject. Edit that catalog and run
`agent-harness/agent-instructions/core-rules/communication/render-enforced-reply-rules-markdown.py` rather than editing
this file, which CI checks character for character against the catalog.
</generated_surface>

<binds_every_human_facing_channel>
These rules hold for every text a human reads, a chat reply, a commit message, a merge request body, a ticket comment, a
report, a published page, not only for the live keyboard reply where a hook checks them. Never use an em dash or an en
dash in prose; recast with a comma, a colon, or two sentences. Never open with a reaction or a sycophancy phrase ("You
are right", "Good catch", "Sure", "Of course"). Never open by narrating what you are about to do ("Let me", "I will go
ahead"). Give the link for any merge request or pull request you name, so the user clicks through to validate it.
</binds_every_human_facing_channel>
