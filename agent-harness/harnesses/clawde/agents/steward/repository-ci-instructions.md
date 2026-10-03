### Repo ci tooling

Watch CI with `glab`: `glab ci list --sha $(git rev-parse HEAD) --output json` finds pipelines for a commit. Start a
background watcher, inspect every job, and verify the terminal pipeline status with
`glab ci get --pipeline-id <id> --output json`; only `success` is green. A short sha matches no pipeline and a
just-pushed commit can have none for a few seconds, so use the full sha and retry an empty list.

The integration and runtime tiers need the live machine, so a nightly 03:00 job owns them and no tick of yours ever runs
them; a red night is repo breakage you fix like a red CI. It reaches you as an inbox message from `nightly-deep-tiers`
carrying the verdict and the log path (`~/.local/state/dotfiles-nightly-tests/nightly-deep-test-tiers.log`). Read that
log, run the failing test files directly, fix and push when the cause is in the tree, and otherwise report the tier and
the failing test names to the human through notify. A passing night sends nothing.
