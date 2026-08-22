<amend-only-your-own-head>
A live peer can commit between your commit and a later amend. Before `git commit --amend`, verify that `HEAD` is still
the commit you just created and belongs to this task. If it moved, do not amend: changing the new head rewrites a peer's
commit rather than yours.
</amend-only-your-own-head>

<a-user-edit-may-live-in-another-worktree>
When someone says they changed or deleted a file and the main checkout shows it untouched, that is not evidence the edit
never saved. Several live worktrees run in parallel here and an edit lands in whichever one happened to be open. Treat
the claim as a search instruction across every worktree rather than a claim to verify in one, and remember that
uncommitted state in a sibling worktree is real work belonging to someone else, so read it and never revert it.
</a-user-edit-may-live-in-another-worktree>
