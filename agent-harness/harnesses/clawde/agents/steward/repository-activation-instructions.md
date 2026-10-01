### Standing activation permission

The operator authorizes routine rebuilds on this machine whenever its configuration changes, including during active
use. This standing permission replaces the upstream steward skill's idle-window and published-revision prerequisites for
local activation. Keep publication subject to the repository's CI requirements. Shared Herdr server activation still
requires its separate explicit approval.

### Independent maintenance progress

A dirty checkout, committed divergence, or unavailable GitHub access can block synchronization without blocking local
evaluation and rebuilding. Preserve uncommitted work; never stage, stash, reset, or discard it to clear a maintenance
gate. Build the available local configuration when it changes, and distinguish that result from being synchronized with
the latest upstream revision. Attempt safe synchronization again when remote access returns.

The heartbeat checks local activation before deciding whether a model turn is needed, including cycles blocked on remote
access or reconciliation. Read the activation result each turn. Report a concrete build failure or unavailable upstream
access; never turn either into a blanket decision to skip every independent maintenance step.

### Detached rebuild execution

For this repository, use `steward-rebuild --state-directory ~/clawde/steward/state/rebuild` for local activation on both
macOS and NixOS. It evaluates the desired system, skips an unchanged system, and otherwise detaches the ordinary
`rebuild` command with its existing serialization. It verifies the live system against the evaluated result and records
`rebuild-result.json` and `rebuild.log` in that directory. It replaces `steward-activate` and machine-local activation
scripts for this operation. Read its result on the next tick; never treat launch as completion.

A failed rebuild remains owed work: inspect its log, fix the concrete failure, and retry after the cause changes. A
successful rebuild records local activation only; it provides no evidence that a fetch, push, or CI run succeeded.
