<the_index_is_shared_with_live_peers>
This repository is worked concurrently by other agents sharing one working tree and one index, so staging is not
private: a peer can stage their files between your add and your commit, and a bare commit then swallows their work into
yours. The hazard runs both ways, and the reverse is the confusing one, since a peer's bare commit can carry off files
you staged and never mention it. Commit with explicit pathspecs, which commits only those paths regardless of what else
sits staged, and read the staged list immediately before committing while expecting it to name files you never touched.
Never stage with a blanket add.
</the_index_is_shared_with_live_peers>

<a_user_edit_may_live_in_another_worktree>
When someone says they changed or deleted a file and the main checkout shows it untouched, that is not evidence the
edit never saved. Several live worktrees run in parallel here and an edit lands in whichever one happened to be open.
Treat the claim as a search instruction across every worktree rather than a claim to verify in one, and remember that
uncommitted state in a sibling worktree is real work belonging to someone else, so read it and never revert it.
</a_user_edit_may_live_in_another_worktree>

<moving_a_worktree_that_contains_submodules>
`git worktree move` hard-refuses when the worktree contains submodules, so relocating one means a plain move followed by
a repair. The repair fixes only the worktree's own git file: the submodule's git file still holds a relative gitdir
computed for the old directory depth, and the corresponding pointer back from the repository's module directory is also
stale. Each fails loudly on the next status call, so fix both by hand after the move rather than assuming the repair
covered them.
</moving_a_worktree_that_contains_submodules>
