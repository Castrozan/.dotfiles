---
name: background-waits
description: Track background Bash and Monitor waits that stayed silent, deny their shape in the wait guard, and widen its allowlist. Use when a background command never notified or a good wait was denied.
---

### Ownership

The wait guard lives in the dotfiles repository's PreToolUse hooks. Its module `background_wait_shape_classifier`
decides for backgrounded Bash and Monitor alike, and two corpora pin it: `known_silent_background_waits` lists waits
the guard must deny, `known_good_tool_calls` lists calls no guard may deny. Each corpus has an integration test that
runs the whole PreToolUse dispatcher. Work in that repository and follow its commit, review and rebuild rules.

### Tracking

Run `background-wait-tracker scan`, then `background-wait-tracker list`; `--help` owns the flags. The tracker reads
Claude Code transcripts because no hook fires when a background task ends or while a session sits waiting. The
transcript is the only record that holds the launch, its task id and the completion notification together.

A command is recorded only with proof of silence. Proof is a first notification that came late, a `TaskStop` by the
agent, or a harness report of a task still running. A wait whose session simply ended leaves no proof and is never
recorded, so an empty listing does not prove every wait fired.

### Deciding each record

`list` holds records that never notified, that the guard still allows and that nobody dismissed. For each one, `show`
it and read the launch in its transcript. Decide whether the shape cannot notice that what it waits on is gone, or
whether the wait was sound and merely slow.

For a bad shape: 1) add the command to the denied corpus with the rule that should deny it; 2) run that corpus test
and watch it fail; 3) tighten the classifier until it passes. For a sound wait, `dismiss` it with the reason. A record
that already reads `denied` needs nothing.

### Widening the allowlist

When the guard denies a sound wait: 1) add the exact call to the known-good corpus; 2) run its test and see the
denial; 3) widen the matching shape in the classifier, or add a named shape. Name a new shape in the deny text and in
the guidance page the deny text cites. Never widen by deleting a denied corpus entry.

### Traps

Commands in transcripts carry peer names, pane ids, hosts and paths from private work, and both corpora are committed
to a public repository. Rewrite those to neutral values before adding an entry, keeping the shape intact.

The classifier sees only command text, so a wait hidden inside a script file reads as `not-a-wait`. Record the
script's loop as the corpus entry, not its path.

Run both corpus tests after every classifier change. A rule widened to catch one silent wait denies ordinary polls
with it, and only the known-good corpus shows that.
