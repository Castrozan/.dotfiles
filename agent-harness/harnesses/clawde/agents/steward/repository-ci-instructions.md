### Repo ci tooling

Use the forge skill for every hosted operation, including retries, in place of provider-specific commands in the
upstream steward skill.

Load the forge and CI watcher skills. Resolve the repository's effective upstream, find runs for the full commit SHA,
and start a background watcher for every required run. Inspect every job and require the provider's terminal successful
verdict. A just-pushed commit can have no run for a few seconds; retry an empty list rather than treating it as green.

The integration and runtime tiers need the live machine, so a nightly 03:00 job owns them and no tick of yours ever runs
them; a red night is repo breakage you fix like a red CI. It reaches you as an inbox message from `nightly-deep-tiers`
carrying the verdict and the log path (`~/.local/state/dotfiles-nightly-tests/nightly-deep-test-tiers.log`). Read that
log, run the failing test files directly, fix and push when the cause is in the tree, and otherwise report the tier and
the failing test names to the human through notify. A passing night sends nothing.
