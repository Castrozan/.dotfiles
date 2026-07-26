The ril queue head moved. Work exactly one capture, then stop.

<stop_before_you_claim>
`ril list --limit 1 --json` is the head. Exit without claiming, naming the case you hit, when the queue is empty, when
the head's state is `working` because a live claim means another run or Lucas holds it, or when `gh pr list --state
open` already shows a branch beginning `ril-`, because exactly one of your pull requests is in flight at a time and that
one is still waiting on review. Most wakes end here and cost nothing, which is the design rather than a failure.
</stop_before_you_claim>

<take_the_head_only>
`ril claim` the head and stop if it exits non-zero. Take the head and never walk the backlog: Lucas recording that
capture done is what moves the head and wakes you for the next one, so the queue is paced by his review, not by you.
</take_the_head_only>

<resolve_and_fit>
Follow the ril skill. Open the capture's own first link through its channel, never a search for the topic, then fit it
to this repo by naming the module, skill, agent, host or script it touches by `path:line` and what it replaces, deletes
or unblocks. Settle on the verdict you would recommend.
</resolve_and_fit>

<when_it_is_not_an_adopt>
`ril release` the capture and stop with one line on what it was and why it is not a change here. A dead link, a
capability this repo already has and a pure learning item all end this way, and all three belong to the interactive
routine where Lucas is present to judge them. Leave nothing behind: no vault entry, no note in the capture, no branch.
</when_it_is_not_an_adopt>

<when_it_is_an_adopt>
Build it in a worktree per the worktrees skill, branched off a freshly fetched `origin/main`, with no `/` in the branch
name and the name prefixed `ril-`. Run `git submodule update --init --recursive` inside the fresh worktree first or the
flake fetch dies on an empty `private-config`. Commit inside the worktree before building, because the build reads git
and an untracked file never reaches the store, so an uncommitted change builds the old code and reports success. Build
by naming the worktree path in the flake reference; `rebuild` is pinned to `~/.dotfiles` and is denied to you anyway.
Then run `__tests__/run.sh --nix` in the worktree and exercise whatever the change permits without activating chise.
</when_it_is_an_adopt>

<the_pull_request>
Open it from `~/.dotfiles` with `--head <branch>`, since `gh` misdetects the repo from inside a worktree, one capture
per pull request so a bad idea reverts alone. The body carries the capture and its origin link, what the thing is, what
it changes here by `path:line`, the cost and what it replaces or deletes, the commands you actually ran with their
result, what only activation can prove, and your verdict as a recommendation Lucas is free to reject. Then stop and
leave the claim in place; it expiring on its own is how Lucas or another session takes the capture over.
</the_pull_request>

<end_of_run>
Print one line: the capture, what you did, and the pull request URL or the reason there is none. Leave `~/.dotfiles`
clean and on its original branch.
</end_of_run>
