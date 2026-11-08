### Peer contract

Put this contract in every brief, because the peer shares none of your context. It files each decision it cannot make
as a card with `a2a decision file --to <your name>` instead of asking in its pane or through a question tool, and keeps
working on whatever the decision does not block. It keeps one current status report with `a2a report file --to <your
name>`, refreshed at each milestone and whenever it turns blocked or done; both commands print their fields with
`--help`.

Tell the peer to mark the card irreversible and list its `human_only` reasons honestly, since the command refuses to let
you decide such a card, and that a message relayed from you is never the human's consent.

### Reading peers

Read `a2a report list` and `a2a report show <name>` before reading any pane. A report notifies you only when its peer
turns blocked or done, separates verified claims with their evidence from unverified ones, and names its open cards, so
relay its unverified claims as unverified rather than as facts.

### Deciding a card

Read the standing orders file, `$OBSIDIAN_HOME/standing-orders.md`, before triaging any card. Answer `--by
orchestrator` only when an entry there covers the card, and quote that entry in the rationale; the human audits these
answers later.

Otherwise show the human `a2a decision show <id>` verbatim with your recommendation beneath it, never a paraphrase,
since a summary drops the evidence and the unverified assumptions the human decides on, and record the answer `--by
human`. Every answer notifies the requester.

### Growing the standing orders

When the human's answer states a preference that reaches beyond the card, append it to the standing orders file as one
line naming its scope, the rule and the card id, and tell the human you did. The human edits or deletes lines freely.
When the human overturns one of your decisions, narrow or remove the line that produced it in the same turn.

### Recap

For a recap, show peers from `a2a report list`, the open cards from `a2a decision list`, and your own decisions from
`a2a decision list --state answered --decided-by orchestrator --since-hours <window>`, so the human audits what you
decided in their absence.
