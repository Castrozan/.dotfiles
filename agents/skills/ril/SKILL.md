---
name: ril
description: Work the ReadItLater capture queue into machine changes and filed knowledge, one capture at a time, with the user deciding every verdict. Use for ril, RIL, ReadItLater, the capture inbox, saved links, "process what I saved".
---

<what_this_produces>
The capture inbox is not an annotation backlog. Every capture ends as a change to this repo, a deliberate thing to
learn, or a filed reference, never as a summary appended to the capture. A pass that leaves the machines and the brain
unchanged has failed no matter how many captures it marked done.
</what_this_produces>

<queue>
`ril list` gives the working order, newest first, because a recent capture is still actionable while a year-old one is
usually already obsolete or already adopted. The capture file is its own progress record: no marker means unworked, a
live `status:: working` means someone holds it, `#agent-work-done` means finished. So the routine resumes in any session
on any host, and a side queue file would desynchronize the moment a capture is worked elsewhere. `ril list --claimable`
hides what another run holds, `--json` feeds a script.
</queue>

<claim_before_working>
`ril claim` a capture before touching it and `ril release` it when abandoning it unfinished. A claim exits non-zero when
another run already holds it, and obeying that non-zero is the entire mutual exclusion between this session and the
chise watcher: stop and take the next capture instead of forcing a takeover. A claim older than the expiry reads as
stale and is reclaimed without any flag, which is how a crashed run frees its capture with no cleanup step.
</claim_before_working>

<one_at_a_time>
Take a single capture from resolve to filed before opening the next, and hold at the decision gate rather than queueing
several proposals. Never rate a capture from its stub: the stub is a shortened link plus a truncated quote, and rating
that is the failure mode this routine exists to replace.
</one_at_a_time>

<resolve_the_origin>
The first link in the capture body is the canonical source. Open that, never a search for the topic. Route by channel:
x.com through the twitter skill for thread and quote context, YouTube through the youtube skill for the transcript, an
ordinary article through `curl -sS`, and anything that serves an empty shell to `curl` because it renders client side or
sits behind a login, Instagram and LinkedIn among them, through the already logged-in browser over chrome-devtools.
Never WebFetch, whose summarizer tampers with the content. Reach for the research skill only after the origin is read,
when the idea outgrows the one source that captured it. A dead link is a drop with the reason recorded, never a guess
reconstructed from the title.
</resolve_the_origin>

<fit_to_the_setup>
The question is never whether the thing is good, it is what it changes here. Ground every claim in this repo: name the
module, skill, agent, host or script it touches by `path:line`, and state what it replaces, deletes or unblocks. A
proposal that cannot name a file is a learning item, not an adoption. Prefer the option that deletes code here over the
one that adds a dependency, and say plainly when we already have the capability.
</fit_to_the_setup>

<verdict_gate>
Five outcomes: adopt changes the repo now; trial runs it unpackaged first and decides after; learn creates a study entry
naming what to practice; reference files it with no action; drop discards it with the reason. Present one screen per
capture: what it is, what it changes here, the cost, and a recommended verdict. The user picks. Never self-approve an
adopt, and never soften a drop into a reference to avoid discarding something.
</verdict_gate>

<applying_an_adopt>
An adopt is built in an isolated worktree per the worktrees skill, never on the main checkout, and it is proven before
it is proposed. Initialize submodules inside the fresh worktree first or the flake fetch dies on an empty
`private-config`. Commit inside the worktree before building, because the build reads git and an untracked file never
reaches the store, so it would build the old code and report success. Build that worktree by naming its path in the
flake reference: `rebuild` is pinned to `~/.dotfiles` and would silently build main instead. Then run
`__tests__/run.sh --nix`, exercise the change live, and say in the pull request what you actually ran rather than that
it should work. On chise never switch a bare worktree, since this machine deploys through a private entrypoint the
worktree lacks and a bare switch strips it; build there and leave activation to the review. Open the pull request from
the main checkout with `--head`, one capture per pull request so a bad idea reverts alone, and never merge it.
</applying_an_adopt>

<filing>
Every non-drop capture becomes an entry under the vault Second Brain per its authoritative CONTRIBUTING contract, read
before writing rather than recalled. Tag only from the Tag Legend and extend the Legend before using a new value. The
entry carries what to steal and, for an adopt, the commit that landed it, so the brain records the decision and not just
the link.
</filing>

<marking_done>
`ril record` stamps the marker, the verdict, the outcome and the entry link as queryable inline fields, and it clears
the claim. Never hand-edit a capture to mark it done, and never record a verdict the user has not given. An unmarked
capture is simply unfinished work, which is the property the whole queue depends on.
</marking_done>

<the_chise_watcher>
The `ril-watcher` clawde agent runs the mechanical half unattended: a change gate polls `ril probe` and launches one
run only when the queue head moves, so a new capture produces exactly one pull request. The probe fingerprints the head
and deliberately holds still while the head is claimed, so nothing walks the backlog while a proposal waits for the
user. That agent claims, resolves, fits, builds the worktree proof and opens the pull request, then stops: it never
merges and it never records a verdict. So keep every phase before the gate expressible as a reviewable diff plus an
entry draft, and let no phase before the gate touch the main checkout or the running machine.
</the_chise_watcher>
