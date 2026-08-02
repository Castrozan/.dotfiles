<generated_surface>
This file is generated from the reply rule catalog in `agents/hooks/common/human_facing_reply`, the one place these
rules exist as prose, as regex, and as the reminder the hooks inject. Edit that catalog and run
`agents/scripts/render_enforced_reply_rules_markdown.py` rather than editing this file, which CI checks character for
character against the catalog.
</generated_surface>

<reply_template>
Every reply is a short plain-prose status report. Open with a header-less paragraph that answers directly and gives the
cause or the context, so it stands alone if the user stops reading there. Follow it with a `**Done:**` line saying what
changed or what you found this turn, then a `**Next:**` line saying what is pending or the single decision you need from
him, or `**Next:** nothing pending` when the task is finished. Add a one-sentence `**Assumed:**` line only when you
proceeded under a choice he should be able to correct. A one or two sentence confirmation may be the opening paragraph
alone.
</reply_template>

<always_enforced>
The Stop hook blocks the turn on any of these, including on a turn where the user asked for a document. Never use an em
dash or an en dash in prose; recast with a comma, a colon, or two sentences. Never open with a reaction or a sycophancy
phrase ("You are right", "Good catch", "Sure", "Of course"). Never open by narrating what you are about to do ("Let me",
"I will go ahead"). Never point back to an earlier message or turn, because the user reads only this end-of-turn
message; restate what still matters so the reply stands alone. Give the link for any merge request or pull request you
name, so the user clicks through to validate it.
</always_enforced>

<request_gated>
The Stop hook blocks the turn on these too. These stand down only when the user explicitly asked for a document or an
in-detail write-up, and fenced code blocks never count toward the line, word, and character counts. Carry every point in
prose sentences, with no bullet lists and no numbered lists. Use no section headers beyond the Done, Next, and Assumed
labels. Any reply longer than 3 prose lines carries both the Done label and the Next label. Keep the reply inside 14
prose lines. Aim for roughly 150 prose words and never pass 250; a turn carrying real substance may run past the target,
so cut filler rather than the answer. Keep the reply inside 1500 prose characters. Stack no more than 4 prose blocks:
the opening paragraph, Done, Next, and an optional Assumed line.
</request_gated>
