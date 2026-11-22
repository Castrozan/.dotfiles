### Fix one failing change

Read the fix loop context at `$ARTIFACTS_DIR/fix-loop/context.md` first. It states the task, the scoped test command
and the rules. Then read the latest scoped test output at `$ARTIFACTS_DIR/fix-loop/test.log` and the gate output at
`$ARTIFACTS_DIR/fix-loop/gate.log` when that file exists; an earlier attempt may already have edited the checkout.

Diagnose the cause from that output and the code it names, then edit the checkout so the scoped test passes and the
task is done. Keep the edit inside the task. You may run the scoped test command once to confirm, and nothing broader.

The workflow formats, lints, tests, stages and commits after you. Never run git add, git commit, git stash, git
checkout of other revisions, or a formatter, and never push.

Report in one or two sentences what you changed and why.
