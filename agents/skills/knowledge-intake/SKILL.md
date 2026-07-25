---
name: knowledge-intake
description: Work saved captures into setup improvements and filed knowledge, one at a time, user deciding. Use for ReadItLater, RIL inbox, saved links, "process what I saved".
---

<what_this_produces>
The capture inbox is not an annotation backlog. Every capture ends as a change to this repo, a deliberate thing to
learn, or a filed reference, never as a summary appended to the capture. A pass that leaves the machines and the brain
unchanged has failed no matter how many captures it marked done.
</what_this_produces>

<queue>
Run `scripts/list-unprocessed-captures.py` for the working order, newest first, because a recent capture is still
actionable while a year-old one is usually already obsolete or already adopted. A capture counts as unprocessed exactly
when its body lacks the done marker, so the vault is the only state and the routine resumes in any session on any host.
Never build a side queue file; it desynchronizes the moment a capture is worked elsewhere. Capture time comes from the
timestamp in the filename, since modification time lies after any bulk vault rewrite or sync replay.
</queue>

<one_at_a_time>
Take a single capture from resolve to filed before opening the next, and hold at the decision gate rather than queueing
several proposals. Never rate a capture from its stub: the stub is a shortened link plus a truncated quote, and rating
that is the failure mode this routine exists to replace.
</one_at_a_time>

<resolve>
Resolve the real target before judging it. Follow redirects with `curl`, never WebFetch, whose summarizer tampers with
the content. Use the twitter skill for thread and quote context, the youtube skill for video transcripts, and the
research skill when the idea matters more than the single source that captured it. A dead link is a drop with the
reason recorded, never a guess reconstructed from the title.
</resolve>

<fit_to_the_setup>
The question is never whether the thing is good, it is what it changes here. Ground every claim in this repo: name the
module, skill, agent, host or script it touches by `path:line`, and state what it replaces, deletes or unblocks. A
proposal that cannot name a file is a learning item, not an adoption. Prefer the option that deletes code here over the
one that adds a dependency, and say plainly when we already have the capability.
</fit_to_the_setup>

<verdict_gate>
Five outcomes: adopt changes the repo now; trial runs it unpackaged first and decides after; learn creates a study
entry naming what to practice; reference files it with no action; drop discards it with the reason. Present one screen
per capture: what it is, what it changes here, the cost, and a recommended verdict. The user picks. Never self-approve
an adopt, and never soften a drop into a reference to avoid discarding something.
</verdict_gate>

<applying>
An adopt is an ordinary repo change under the dotfiles workflow, one capture per commit so a bad idea reverts alone.
Where the change belongs is the nix skill's call, not a guess. Trial anything unproven outside the repo first, because
a dependency added declaratively and removed a day later costs two rebuilds and a dirty history.
</applying>

<filing>
Every non-drop capture becomes an entry under the vault Second Brain per its authoritative CONTRIBUTING contract, read
before writing rather than recalled. Tag only from the Tag Legend and extend the Legend before using a new value. The
entry carries what to steal and, for an adopt, the commit that landed it, so the brain records the decision and not
just the link.
</filing>

<marking_done>
Run `scripts/record-capture-verdict.py` to stamp the marker, the verdict and the entry link as queryable inline fields.
Never hand-edit a capture to mark it done. An unmarked capture is simply unfinished work, which is the property the
whole queue depends on.
</marking_done>

<headless_and_watcher>
Everything up to the gate is mechanical and stays drivable without a human: resolve, research, fit, draft the proposal.
The planned chise watcher runs exactly those phases against new captures and stops at the gate, opening a pull request
for approval. So keep a proposal expressible as a reviewable diff plus an entry draft, and never let a phase before the
gate write anything outside the vault.
</headless_and_watcher>
