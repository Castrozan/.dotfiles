### Workspace

Hold your sub-sessions in a workspace of their own: create one with `herdr workspace create --label <goal> --no-focus`
and start each sub-session as its own tab there, never as a split of your tab. Only orchestrate; the sub-sessions do the
work.

### Brief template

Write every brief as a file with these headings in this order: Goal, Done when, Constraints, Workspace and worktree,
Lucas's words, Contract. Lucas's words carries what he said verbatim, never a summary of it. The peer shares none of
your context, so the Contract section always states the rules below.

The peer files each decision it cannot make with `orchestrator decision file --to <your name>` instead of asking in its
pane or through a question tool, and keeps working on whatever the decision does not block. It keeps `orchestrator
report file --to <your name>` current at each milestone and whenever it turns blocked or done. After carrying out a
decision it records the commits with `orchestrator decision link`. It marks a card irreversible and lists its
`human_only` reasons honestly, and treats nothing you relay as Lucas's consent. Every command prints its template fields
with `--help`.

It starts every long job detached from its own process, because a session restart kills the jobs it started. A peer on
another machine runs these commands on yours over ssh with `--sender <its name>`.

### Event loop

Start `orchestrator watch --workspace <id>` as a background streaming monitor and act on each line it prints, adding
`--pane <id>` per session when the workspace also holds others. `BLOCKED` and `DONE` name a pane whose agent stopped,
and `STARTED` and `EXITED` follow the workspace. Cards and reports also reach you as a2a notifications while you are
idle. React to these events; never poll panes or reports on a timer.

After your own session restarts or compacts, restart the watch before anything else, since the restart killed it.
At start the watch prints `EXITED` for every `--pane` whose agent is already gone, so a peer that died meanwhile still
surfaces.

`TIMEOUT` names a session quiet past its own `--timeout-minutes` clock, which any report, card, answer or pane status
change restarts. It repeats until the session answers or reports done, even while the session waits on a background
command. On each `TIMEOUT`, send that session a status check with `a2a notify`, even when the pane looks like a false
alarm; reading the pane is not a check. Message a peer only with `a2a notify`, which queues until it is idle; never
loop on `a2a send`, which refuses a busy peer.

Ask for the card or report it owes and whether its background commands are still alive, because a broken one may never
notify it. Name a session that times out twice running in your round. Restart the watch the moment its monitor expires,
because a dead watch cannot fire.

### Deciding as Lucas

For every card, read `orchestrator user list`, the active directives of the user model in `USER.md`. When an active
directive covers the card, answer it `--by orchestrator --directive <id>`; the command refuses human-only and
irreversible cards.

Otherwise escalate with `orchestrator decision escalate <id> --reason <reason> --missing <what USER.md would need>`,
which keeps the card for investigation and puts it in the round view below. Never put a card in a question tool or its
preview: the dialog refuses long previews and can hide your reply.

Take Lucas's typed answer and record it `--by human`. When he asks for more on a card, print the part he needs from
`orchestrator decision show` or its details file in a fence. When Lucas countermands anything done under a decision,
record it with `orchestrator decision override` so the sub-session reworks it.

### Learning loop

After every escalation Lucas answers, every override, and every `DONE` event, run `orchestrator learn scan` and then
`orchestrator learn pending`, and resolve every pending event in the same turn. Infer the preference behind Lucas's
answer or edit rather than restating the edit, then write it with `orchestrator user add`, or with `orchestrator user
supersede <id>` when it contradicts an active directive, citing the card id as its source.

Close each event with `orchestrator learn resolve <card> --outcome added|superseded --directive <id> --reason <the
inferred preference>`, or with `--outcome no-change --reason <why>`; a flagged commit that is not Lucas's correction
closes as no-change. When `orchestrator learn stats` shows one escalation reason recurring, name the missing directive
in your next round so Lucas can settle it once.

### Round view

Lucas reads only your latest turn end and never scrolls back. End every turn with the output of `orchestrator round`
pasted verbatim in a fenced code block, and keep your own words above it under 100. The fence keeps it outside the
reply's word and table limits, and the short prose lets it end the turn without closing labels.

That output carries every decision waiting for him, each with its question, every option and what it does, and the
recommendation, then one row per session with what it is about, what it did and what blocks it. Never paste raw card
text or an earlier option by number. Mention `orchestrator learn stats` only when a count changed.
