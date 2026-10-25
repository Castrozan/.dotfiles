### Chise maintenance cycle

On chise a deterministic cycle, `steward-cycle`, owns every routine step for the dotfiles checkout and the machine-local
wrapper: fetch, fast-forward, rebase, validation, push, CI reading and activation. It runs every five minutes, holds
heavy work until commits and edits have been quiet for fifteen minutes, and wakes you only when it records a failure in
`~/clawde/steward/state/cycle/attention.json`. Its last decision is in `decision.json` beside it.

### Fix only the named failure

Read `attention.json` and the log or messages it names, fix the cause, commit specific files, and end the turn. Never
push the dotfiles or wrapper repository, rebuild, switch, or build the system yourself: the cycle validates your commit
inside its memory-bounded scope, then pushes and activates it. A system build you start runs outside that bound and lags
the operator's desktop.

### Attention kinds

For `build-red`, `ci-failing` and `activation-failed`, the named log or failing workflow holds the cause; read CI
through the forge skill, and a `build-red` whose cause is a wrapper commit is fixed in the wrapper. For
`rebase-conflict` and `entrypoint-diverged`, rebase the local commits onto their origin by hand and resolve the
conflict, never resetting or force-pushing. For `submodule-pin-unpublished`, publish the pinned submodule commit to its
own remote fast-forward-only. For `inbox`, act on each named message within the steward scope, then move it into
`inbox/read/`.

### When you cannot fix it

When the failure has no cause in the tree, as with `validation-unavailable` from Nix infrastructure or a `cycle-error`
inside the cycle itself, report the kind, revision and detail to the operator through notify and end the turn. For
`synchronization-blocked`, uncommitted edits someone else owns have kept the checkout from syncing for hours: report
the dirty paths through notify and never stage, stash, commit or discard them. An unchanged failure wakes you once
more, then stays silent until it changes.
