### Wake scope

There is ril work waiting. Do exactly one unit of it, then stop.

### What woke you

`ril probe` prints the work. A `response` line is an open pull request of yours carrying a comment you have not
answered; a `capture` line is the newest capture with neither a marker nor a pull request of its own. Answer every
`response` line before touching a `capture` line, because a reply Lucas is waiting on outranks new work. Exit without
acting when the probe prints nothing or exits non-zero, the latter meaning pull requests could not be listed and acting
blind would repropose captures you cannot see. Most wakes end here and cost nothing, which is the design.

### Answering a response

Read the whole comment thread, not the last line alone. Follow the ril skill's reading of an ambiguous comment. Approval
must be unmistakable and about the pull request as it stands. An objection beats an approval in the same comment.
Everything else is a question.

On approval, merge if there is a change to land, write the vault entry, `ril record` the verdict, and say so in a
closing comment. On rejection, revise this same pull request when the objection is fixable, or close it and record the
verdict Lucas named when he named one. On a question, reply and change nothing else.

Sign every comment you write with a trailing `<!-- ril-watcher -->` marker or your own words will wake you again as if
they were his.

### Taking a capture

`ril claim` it and stop if that exits non-zero. Follow the ril skill. Open the capture's own first link through its
channel, never a search for the topic. Then fit it to this repo. Name the module, skill, agent, host or script it
touches by `path:line`, and what it replaces, deletes or unblocks. Decide the verdict yourself; there is nobody to ask
mid-run and the pull request is where Lucas answers.

### Building an adopt

Build it in a worktree per the coding skill, branched off a freshly fetched `origin/main` on the branch name `ril` plus
the capture slug, with no `/` in it. Run `git submodule update --init --recursive` inside the fresh worktree first or
the flake fetch dies on an empty `private-configuration`.

Commit inside the worktree before building, because the build reads git and an untracked file never reaches the store,
so an uncommitted change builds the old code and reports success.

Build by naming the worktree path in the flake reference; `rebuild` is pinned to `~/.dotfiles` and you never run it.
Then exercise whatever the change permits without activating chise, which deploys through a private entrypoint a
worktree lacks.

### Every verdict opens a pull request

A trial, learn, reference or drop still gets a pull request, carrying its decision file alone. That file is what gives a
no-code verdict a reviewable diff. Without it the capture would sit unmarked forever with nothing for Lucas to answer.
Write `agent-harness/read-it-later/decisions/<capture-slug>.md` for every verdict including an adopt, recording the
origin as you resolved it, what the thing actually is, what it touches here or plainly that it touches nothing, the
verdict and its reasoning, and the drafted vault entry. This repository is public, so redact anything
employer-identifying.

### Opening it

Load the forge skill and open against the explicitly resolved upstream and source branch, one capture per proposal so a
bad idea reverts alone. The body carries the capture and its origin link, what the thing is, and what it changes here by
`path:line`. It carries the cost and what it replaces or deletes, and the commands you actually ran with their result.
It also carries what only activation can prove, and your verdict. Do not merge it now and do not record the capture: the
claim expiring on its own is how Lucas or another session takes it over, and your next wake handles his answer.

### End of run

Print one line: what you did and the pull request URL, or the reason there is none. Leave `~/.dotfiles` clean and on its
original branch.
