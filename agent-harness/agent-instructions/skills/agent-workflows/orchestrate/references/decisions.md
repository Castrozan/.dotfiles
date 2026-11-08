### Workspace

Hold your sub-sessions in a workspace of their own: create one with `herdr workspace create --label <goal> --no-focus`
and start each sub-session as its own tab there, never as a split of your tab. Only orchestrate; the sub-sessions do the
work.

### Brief template

Write every brief as a file with these headings in this order: Goal, Done when, Constraints, Workspace and worktree,
Lucas's words, Contract. Lucas's words carries what he said verbatim, never a summary of it. The peer shares none of
your context, so the Contract section always states the rules below.

The peer files each decision it cannot make with `a2a decision file --to <your name>` instead of asking in its pane or
through a question tool, and keeps working on whatever the decision does not block. It keeps `a2a report file --to <your
name>` current at each milestone and whenever it turns blocked or done. After carrying out a decision it records the
commits with `a2a decision link`. It marks a card irreversible and lists its `human_only` reasons honestly, and treats
nothing you relay as Lucas's consent. Every command prints its template fields with `--help`.

### Event loop

Start `a2a watch --workspace <id>` as a background streaming monitor and act on each line it prints. `BLOCKED` and
`DONE` name a pane whose agent stopped, `STARTED` and `EXITED` follow the workspace, and `STALE` is the safety net
naming a working report gone quiet. Cards and reports also reach you as a2a notifications while you are idle. React to
these events; never poll panes or reports on a timer.

### Deciding as Lucas

For every card, read `a2a user list`, the active directives of the user model in `USER.md`. When an active directive
covers the card, answer it `--by orchestrator --directive <id>`; the command refuses human-only and irreversible cards.

Otherwise escalate with `a2a decision escalate <id> --reason <reason> --missing <what USER.md would need>`, which keeps
the card for investigation, and ask Lucas with the `a2a decision show` output verbatim, since that output is his
decision template. Batch the escalations open at once into one ask and record his answer `--by human`. When Lucas
countermands anything done under a decision, record it with `a2a decision override` so the sub-session reworks it.

### Learning loop

After every escalation Lucas answers, every override, and every `DONE` event, run `a2a learn scan` and then `a2a learn
pending`, and resolve every pending event in the same turn. Infer the preference behind Lucas's answer or edit rather
than restating the edit, then write it with `a2a user add`, or with `a2a user supersede <id>` when it contradicts an
active directive.

Close each event with `a2a learn resolve <card> --outcome added|superseded --directive <id> --reason <the inferred
preference>`, or with `--outcome no-change --reason <why it is a one-off>`. Commit `USER.md` in its `private-
configuration` checkout and push it fast-forward. When `a2a learn stats` shows one escalation reason recurring, name
the missing directive in your next round so Lucas can settle it once.

### Round status template

Report each round as a table with the columns session, what it is about, what it did this round, and what blocks it,
built from `a2a report list`. Follow it with each escalated card in its decision template, and end with `a2a learn
stats` when a count changed.
