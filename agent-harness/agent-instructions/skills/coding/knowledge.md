<the-index-is-shared-with-live-peers>
This repository is worked concurrently by other agents sharing one working tree and one index, so staging is not
private: a peer can stage their files between your add and your commit, and a bare commit then swallows their work into
yours. The hazard runs both ways, and the reverse is the confusing one, since a peer's bare commit can carry off files
you staged and never mention it. Commit with explicit pathspecs, which commits only those paths regardless of what else
sits staged, and read the staged list immediately before committing while expecting it to name files you never touched.
Never stage with a blanket add.
</the-index-is-shared-with-live-peers>

<amend-only-your-own-head>
A live peer can commit between your commit and a later amend. Before `git commit --amend`, verify that `HEAD` is still
the commit you just created and belongs to this task. If it moved, do not amend: changing the new head rewrites a peer's
commit rather than yours.
</amend-only-your-own-head>

<agent-trailers-are-hook-owned>
The commit hook stamps agent provenance such as harness, machine, session, and resume metadata. Never author or edit
those trailers manually: doing so records a session identity that may not exist and makes provenance untrustworthy.
Inspect the repository's harness tooling when provenance needs to be read rather than reconstructing the trailer format
from memory.
</agent-trailers-are-hook-owned>

<a-user-edit-may-live-in-another-worktree>
When someone says they changed or deleted a file and the main checkout shows it untouched, that is not evidence the edit
never saved. Several live worktrees run in parallel here and an edit lands in whichever one happened to be open. Treat
the claim as a search instruction across every worktree rather than a claim to verify in one, and remember that
uncommitted state in a sibling worktree is real work belonging to someone else, so read it and never revert it.
</a-user-edit-may-live-in-another-worktree>

<moving-a-worktree-that-contains-submodules>
`git worktree move` hard-refuses when the worktree contains submodules, so relocating one means a plain move followed by
a repair. The repair fixes only the worktree's own git file: the submodule's git file still holds a relative gitdir
computed for the old directory depth, and the corresponding pointer back from the repository's module directory is also
stale. Each fails loudly on the next status call, so fix both by hand after the move rather than assuming the repair
covered them.
</moving-a-worktree-that-contains-submodules>
