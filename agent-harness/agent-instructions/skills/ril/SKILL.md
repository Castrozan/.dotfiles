---
name: ril
description: Work the ReadItLater capture queue into machine changes and filed knowledge, one capture at a time, deciding each verdict live with the user or at a pull request. Use for ril, RIL, ReadItLater, the capture inbox, saved links, "process what I saved".
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
Take a single capture from resolve to filed before opening the next. Interactively that means holding at the decision
gate rather than queueing several proposals at the user. Unattended it means one capture per run and one capture per
pull request, so a bad idea reverts alone, while captures already awaiting a response are simply skipped rather than
waited on. Never rate a capture from its stub: the stub is a shortened link plus a truncated quote, and rating that is
the failure mode this routine exists to replace.
</one_at_a_time>

<resolve_the_origin>
The first link in the capture body is the canonical source. Open that, never a search for the topic. Route by channel:
x.com through the twitter skill for thread and quote context, YouTube through the youtube skill for the transcript, an
ordinary article through `curl -sS`, and anything that serves an empty shell to `curl` because it renders client side or
sits behind a login, Instagram and LinkedIn among them, through an already logged-in browser. Interactively that is
chrome-devtools against the user's live browser, never the browser skill. Reserve the browser skill for unattended
runs, because chrome-devtools drives the user's own session and stalls the run waiting on an approval nobody is there
to give. Never WebFetch, whose summarizer tampers with the content. Reach for the research skill only after the origin
is read, when the idea outgrows the one source that captured it. A dead link is a drop with the reason recorded, never a
guess reconstructed from the title.
</resolve_the_origin>

<fit_to_the_setup>
The question is never whether the thing is good, it is what it changes here. Ground every claim in this repo: name the
module, skill, agent, host or script it touches by `path:line`, and state what it replaces, deletes or unblocks. A
proposal that cannot name a file is a learning item, not an adoption. Prefer the option that deletes code here over the
one that adds a dependency, and say plainly when we already have the capability.
</fit_to_the_setup>

<verdict_gate>
Five outcomes: adopt changes the repo now; trial runs it unpackaged first and decides after; learn creates a study entry
naming what to practice; reference files it with no action; drop discards it with the reason. Two decision surfaces
carry them. Interactively only the user chooses the verdict: the agent recommends one but never self-approves it. Show
one screen per capture, what it is, what it changes here, the cost and a recommended verdict, and let the user pick
before anything is written. Unattended, the pull request is the decision surface and the watcher decides alone, because
a run that stops to ask has no one to ask. Never soften a drop into a reference to avoid discarding something, and never
open a second pull request to re-litigate a verdict the user already rejected.
</verdict_gate>

<applying_an_adopt>
An adopt is built in an isolated worktree per the coding skill, never on the main checkout, and it is proven before
it is proposed. Initialize submodules inside the fresh worktree first or the flake fetch dies on an empty
`private-configuration`. Commit inside the worktree before building, because the build reads git and an untracked file
never reaches the store, so it would build the old code and report success. Build that worktree by naming its path in
the flake reference. Never run `rebuild` for the worktree: it is pinned to `~/.dotfiles` and would silently build main
instead. Exercise the change live, and say in the pull request what you actually ran rather than that it should work.
On chise never switch a bare
worktree, since this machine deploys through a private entrypoint the worktree lacks and a bare switch strips it; build
there and leave activation to the review. Open the pull request from the main checkout with `--head`, one capture per
pull request so a bad idea reverts alone, and merge it only as the execution of an approving review, never on your own
judgement and never to clear a stale-looking queue.
</applying_an_adopt>

<filing>
Every non-drop capture becomes an entry under the vault Second Brain per its authoritative CONTRIBUTING contract, read
before writing rather than recalled. Tag only from the Tag Legend and extend the Legend before using a new value. The
entry carries what to steal and, for an adopt, the commit that landed it, so the brain records the decision and not just
the link.
</filing>

<marking_done>
`ril record` stamps the marker, the verdict, the outcome and the entry link as queryable inline fields, and it clears
the claim. Never hand-edit a capture to mark it done. Record only a verdict the user gave, live in an interactive pass
or as a pull request approval, never one merely recommended and still awaiting a response. An unmarked capture is simply
unfinished work, which is the property the whole queue depends on.
</marking_done>

<the_chise_watcher>
The `ril-watcher` clawde agent runs the routine unattended and autonomously: it resolves, fits, decides its own verdict,
and answers to the user only through pull requests. A change gate polls `ril probe` and wakes it when there is work,
which is either a capture carrying no marker and no open pull request, or a response from the user on one of its open
pull requests. It takes the newest such capture rather than holding at the head, so an unanswered pull request parks
that capture alone and never dams the queue behind it. It may merge and it may record, but only ever as the execution of
a decision the user already gave on the pull request. It never activates a machine: chise deploys through a private
entrypoint a worktree lacks, so it builds and proves, and leaves switching to the review.
</the_chise_watcher>

<every_capture_ends_at_a_pull_request>
Unattended, each capture gets one pull request whatever the verdict, because a verdict that produces no pull request
leaves the user nothing to answer and strands the capture unmarked forever. An adopt carries the proven change plus its
decision file. A trial, learn, reference or drop carries the decision file alone, which is what gives a no-code verdict
a reviewable diff. The decision file is in `agent-harness/read-it-later/decisions/`. It is named from the capture
date and slug. It records the origin as resolved, what the thing actually is, what it touches here by `path:line`
or plainly that it touches nothing, the verdict and its reasoning, and the drafted vault entry. That log is the
git-backed audit trail the vault cannot be, since the vault is not a git repository. It is a public repository, so
apply the humanize skill's public-repository safeguard before writing it.
</every_capture_ends_at_a_pull_request>

<the_pull_request_conversation>
The user answers in an ordinary pull request comment written in plain language, with no keyword, prefix or syntax to
remember, and the watcher reads the intent. Do not migrate this to GitHub review states: the watcher pushes under the
user's own account, so every pull request it opens is self-authored and GitHub forbids approving or requesting changes
on your own pull request, leaving the comment box as the only channel that exists. Read a comment as one of three
things. Approval means execute the verdict as proposed: merge when there is a change to land, write the vault entry,
`ril record`, and move on. Rejection means do not land it, so read what the user objected to and either revise this same
pull request or, when they name a different verdict, close it and record that one. Anything else is a question, so
answer it in a reply and change nothing else.
</the_pull_request_conversation>

<reading_an_ambiguous_comment>
Interpreting free text is the one place this loop can do real damage, since a misread of hesitation as approval merges
something the user did not want. So bias every uncertain reading toward asking. Approval has to be unmistakable and
about this pull request as it stands; praise for the idea, a question that happens to sound positive, or an approval
hedged on a change you have not made yet are all questions, not approvals. When a comment carries both an objection and
an approval, the objection wins. Never treat silence, a reaction emoji, or your own earlier comment as an answer, and
sign every comment you write with a trailing `<!-- ril-watcher -->` marker so your own replies are never mistaken for
the user's and never re-trigger your gate.
</reading_an_ambiguous_comment>
