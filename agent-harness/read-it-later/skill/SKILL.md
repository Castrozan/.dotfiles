---
name: ril
description: Triage the ReadItLater capture inbox into one pull request per topic group and execute Lucas's answer on it. Use for RIL, saved links, the capture inbox, or a ril-group pull request.
---

### Outcome

Every capture ends dropped, filed in the Second Brain, or dispatched to a work session, and only Lucas decides which, on
a group pull request. Never summarize, rate or tag a capture in place: an annotated capture reads as worked while nothing
changed. Captures are inputs, so a session may still conclude its capture was already covered.

### Queue states

A capture carries no marker while unworked, a live `status:: working` claim while one run holds it, and
`#agent-work-done` once recorded. A capture listed in an open group's decision file is awaiting Lucas. Only `ril apply`
and `ril record` write the done marker; never hand-edit it. `ril claim` answering `held` means another run owns that
capture, so leave it, while `already-done` means it needs nothing more.

### The loop

1\) `ril gather --output FILE` reads every pending capture no open group lists, with its origin and evidence; 2) you
write a cards file and `ril propose --cards FILE` validates it, then opens or extends group pull requests; 3) Lucas
answers on the pull request later; 4) `ril apply --pull-request N --approval-comment ID` executes the covered cards and
merges. `ril propose --example` prints a valid cards document; copy its shape rather than recalling it.

### Reading origins

Judge a capture from its gathered origin, never from the stub. An origin marked `needs_browser` is login-walled,
client-rendered or image-only: read it through `chrome-devtools` in the logged-in browser per the browser skill, and when
Chrome asks to allow the remote debugging connection, click Allow with computer use per the desktop skill. Never use
WebFetch, whose summarizer alters the text. A dead origin is a `drop` whose reason says so, never a guess from the title.

### Triage judgment

Group captures by the work they would feed, not by platform; one group becomes one pull request and one bundle goal.
`drop` when the evidence shows it already landed, is obsolete, or moves nothing Lucas runs. `file` when it is worth
keeping as reference: draft the entry with a title shaped `Creator - Subject`, its theme MOC, tags from the Tag Legend
and what to steal. `session` when it should move a system (dotfiles, kira AI First, avatar, media workers, private
APIs); all session cards of a group share one session with its host, done-when and constraints.

### Card evidence

Cite only what gather or your own reading found: commits, pull requests, existing tools by path, Second Brain entries.
Lucas's own note on a capture outranks your reading of it and goes on the card verbatim. Say whether it runs locally on
chise. Never invent coverage to justify a drop.

### Grouping and deduplication

Before opening a group, compare every capture with `open_groups` from gather. A capture related to an open group joins
it: set that group's `target_pull_request`, keep its topic slug and title, and extend its bundle goal so the related
notes build one complete piece of work. Never open a second pull request on a topic that already has one. A capture a
closed pull request already decided is a `drop` unless the origin brings something new.

### Second Brain

Gather emits the Second Brain index: every MOC and every entry with its theme and source URL. An entry whose source
matches the capture is covered evidence. An entry or MOC that states Lucas's direction, such as his workflows note for
agent work, goes in `second_brain_direction` on every card it bears on, and shapes the proposed action.

### Pull request conversation

Lucas answers in plain language with no syntax to remember. Approval must be unmistakable and about the pull request as
it stands; praise for the idea, a positive-sounding question, or approval hedged on a change not yet made are questions.
An objection beats an approval in the same comment. Silence, a reaction, or your own comment is never an answer. Answer
a question in a reply and change nothing else.

### Per card changes

When Lucas changes cards ("drop 3", "file 2", "session on kira"), rewrite those cards with the same capture names and
run `ril propose` with the group's `target_pull_request`. A rewritten card keeps its place under his approval, while a
newly added capture is not covered by any approval older than it. Sign every comment you write with a trailing
`<!-- ril-watcher -->` so it never reads as his and never wakes the gate.

### Applying

Run `ril apply` with the id of the approving comment, after applying any per-card changes from that comment. It skips
captures already done, records each capture only after its action is confirmed, launches one Claude session per
bundle, and merges only when every card settled. Exit 2 means not merged: comment what is left, such as captures the
approval does not cover or a failed card, and ask. Rerunning after a fix is safe.

### Working a group with Lucas

Interactively, show Lucas the decision table from the pull request, take his per-card changes, and re-propose them as
above. When he approves in the session, post his words verbatim as a pull request comment without the marker, so the
thread records the decision, then run `ril apply` with that comment's id.

### Unattended watcher run

The `ril-watcher` wakes when `ril probe` prints work: a `response` line is an unanswered comment on an open group, a
`capture` line means pending captures no group lists. Exit without acting when the probe prints nothing or fails.
Answer every response before triaging captures; gather and propose all pending captures in one run. Leave
`~/.dotfiles` clean and on its branch; `ril propose` works in its own worktree.

### Public repository

Decision files and pull requests are public. Lucas's capture notes may appear; anything private or employer-identifying
must not, and the commit guard rejects employer names.
