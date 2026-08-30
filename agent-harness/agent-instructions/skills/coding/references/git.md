<context_gathering>
Before a Git mutation, establish the intended repository and inspect status, staged and unstaged diffs, and enough
recent history to understand the local commit convention. Read actual diffs; filenames and summaries are not sufficient
evidence of what a commit contains. Keep every operation scoped to the intended repository even when the shell or
harness can drift between working directories.
</context_gathering>

<analysis>
For each changed file determine what changed, why it matters, its scope, and its impact on callers or dependencies.
Separate task-owned changes from unrelated user or peer work before staging or committing.
</analysis>

<format>
Use the repository's existing commit convention. When it uses Conventional Commits, write `type(scope): subject` in
imperative mood, lowercase, without a period, and keep the subject within 72 characters. Include a body when the change
is non-obvious, combines related concerns, or carries a breaking consequence.
</format>

<staging>
Stage only explicit task-owned paths, never blanket-add the working tree. Verify staged content against intent
immediately before committing. In a shared index, commit with explicit task-owned pathspecs so a peer staging between
your add and commit cannot be swallowed into your commit; read `references/knowledge.md` for the concurrency traps.
</staging>

<commit_discipline>
Commit cohesive changes in small units that can be understood and reverted independently. Do not amend until you have
verified that `HEAD` is still your own commit; a peer may have committed into the shared working tree since your last
command. Harness-generated provenance or commit trailers are hook-owned metadata and must never be written, copied, or
edited by hand.
</commit_discipline>

<history>
Use `git-history` for exploratory history searches that benefit from a cached layered dump. For one targeted lookup, use
the direct Git command; read `references/history.md` for the search method and `references/knowledge.md` for repository
traps.
</history>

<red_flags>
Never stage unrelated files, commit secrets, overwrite peer work, infer a commit from filenames alone, or retry a failed
Git operation by broadening its scope. Verify the actual diff and resulting commit before reporting success.
</red_flags>
