### Review one fix

Read the task in `$ARTIFACTS_DIR/fix-loop/context.md`, then the whole change in `$ARTIFACTS_DIR/fix-loop/change.diff`
with one read of that file; never inspect the changed files one by one. Open a source file only when the diff alone
cannot settle a concern. Read only; change no file.

Apply every lens in this one pass: whether the change does the task and only the task, correctness and edge cases,
whether a test covers the fixed behavior, and the repository's own rules for the touched files.

Report each concern that should be fixed or judged before the change is pushed, with the file and line from the diff.
Rate a defect that breaks behavior, security or the task as critical or high, and anything a person may accept as
medium or low. Try to refute each concern first and report none when the change is sound. Keep each detail under 60
words.
