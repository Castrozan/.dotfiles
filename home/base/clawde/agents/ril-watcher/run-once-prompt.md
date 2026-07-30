There is ril work waiting. Do exactly one unit of it, then stop.

<what_woke_you>
`ril probe` prints the work. A `response` line is an open pull request of yours carrying a comment you have not
answered; a `capture` line is the newest capture with neither a marker nor a pull request of its own. Answer every
`response` line before touching a `capture` line, because a reply Lucas is waiting on outranks new work. Exit without
acting when the probe prints nothing or exits non-zero, the latter meaning pull requests could not be listed and acting
blind would repropose captures you cannot see. Most wakes end here and cost nothing, which is the design.
</what_woke_you>

<answering_a_response>
Read the whole comment thread, not the last line alone, and follow the ril skill's reading of an ambiguous comment:
approval must be unmistakable and about the pull request as it stands, an objection beats an approval in the same
comment, and everything else is a question. On approval, merge if there is a change to land, write the vault entry,
`ril record` the verdict, and say so in a closing comment. On rejection, revise this same pull request when the
objection is fixable, or close it and record the verdict Lucas named when he named one. On a question, reply and change
nothing else. Sign every comment you write with a trailing `<!-- ril-watcher -->` marker or your own words will wake you
again as if they were his.
</answering_a_response>

<taking_a_capture>
`ril claim` it and stop if that exits non-zero. Follow the ril skill: open the capture's own first link through its
channel, never a search for the topic, then fit it to this repo by naming the module, skill, agent, host or script it
touches by `path:line` and what it replaces, deletes or unblocks. Decide the verdict yourself; there is nobody to ask
mid-run and the pull request is where Lucas answers.
</taking_a_capture>

<building_an_adopt>
Build it in a worktree per the worktrees skill, branched off a freshly fetched `origin/main` on the branch name `ril`
plus the capture slug, with no `/` in it. Run `git submodule update --init --recursive` inside the fresh worktree first
or the flake fetch dies on an empty `private-config`. Commit inside the worktree before building, because the build
reads git and an untracked file never reaches the store, so an uncommitted change builds the old code and reports
success. Build by naming the worktree path in the flake reference; `rebuild` is pinned to `~/.dotfiles` and you never
run it. Then exercise whatever the change permits without activating chise, which deploys through a private entrypoint
a worktree lacks.
</building_an_adopt>

<every_verdict_opens_a_pull_request>
A trial, learn, reference or drop still gets a pull request, carrying its decision file alone; that file is what gives a
no-code verdict a reviewable diff, and without it the capture would sit unmarked forever with nothing for Lucas to
answer. Write `ril/decisions/<capture-slug>.md` for every verdict including an adopt, recording the origin as you
resolved it, what the thing actually is, what it touches here or plainly that it touches nothing, the verdict and its
reasoning, and the drafted vault entry. This repository is public, so redact anything employer-identifying.
</every_verdict_opens_a_pull_request>

<opening_it>
Open from `~/.dotfiles` with `--head <branch>`, since `gh` misdetects the repo from inside a worktree, one capture per
pull request so a bad idea reverts alone. The body carries the capture and its origin link, what the thing is, what it
changes here by `path:line`, the cost and what it replaces or deletes, the commands you actually ran with their result,
what only activation can prove, and your verdict. Do not merge it now and do not record the capture: the claim expiring
on its own is how Lucas or another session takes it over, and your next wake handles his answer.
</opening_it>

<end_of_run>
Print one line: what you did and the pull request URL, or the reason there is none. Leave `~/.dotfiles` clean and on its
original branch.
</end_of_run>
