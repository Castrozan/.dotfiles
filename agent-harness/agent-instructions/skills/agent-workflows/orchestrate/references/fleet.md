### Quiet continuity

Use `a2a fleet status` first for persisted fleet evidence. It makes no network calls and emits no notifications. State
lives in `~/.local/state/dot-fleet/registry.sqlite3`, or beneath `XDG_STATE_HOME`. Use `a2a fleet --db PATH ...` for an
isolated registry. The thin `dot-fleet` executable accepts the same arguments without the `a2a fleet` prefix.

Never report every routine agent action; answer the requested status question and surface relevant
blockers or useful milestones.

### Confirmed discovery

Register only a reviewed host mapping with `a2a fleet confirm-host HOST --transport SSH_ALIAS --evidence REFERENCE`;
use `local` as the transport for the confirmed collector host. Confirmation is not a health check. Refresh explicitly
with `a2a fleet status --refresh HOST OTHER_HOST`: at most four hosts, sequentially, two metadata commands per host,
five seconds per command, two MiB output, thirty seconds total network budget, no retries or inference.

A verification worker can supply `a2a fleet ingest HOST FILE`. The JSON has `observed_at` as the original Unix timestamp,
`evidence` as a reference, `a2a` as the exact `a2a list --json` object, and `herdr` as the complete `herdr api snapshot`
reply. Imported observations stay cached. Never read private session stores or insert guessed peer/session IDs.

### Identity and evidence

A target is the tuple of confirmed host, structural pane ID and Herdr-reported conversation ID. Display names may drift.
Path-only session references remain unknown and cannot authorize dispatch. Assign an observed conversation with
`a2a fleet assign HOST PANE_ID SESSION_ID --owner dot --task TASK_REF`. Rotation preserves history without inheriting
ownership. Status returns counts and a 500-row bound per collection so truncation is explicit.

Read `view`, `last_seen`, `age_seconds`, `fresh`, `present` and host `observation` together. Cached can be recent;
unreachable retains last-known agent state; failed observation does not imply failed work. Freshness means metadata
at most five minutes old, never provider productivity. Readiness fields are separate from idle state, and
`delivery_readiness: unverified` means composer acceptance is still unproved.

### Create and resume

Check the target's installed Herdr help before creating a session. Herdr 0.9.1 exposes
`herdr agent start NAME --kind codex --pane OWNED_PANE --timeout 30000`, requiring an existing shell pane; older
`agent start --cwd ... --tab ...` forms are incompatible. Use a target-local isolated worktree and an owned pane in the
pinned orchestration tab without stealing focus. Record returned IDs and wait for interactive readiness with a deadline.

Reuse fitting sessions. Resume only an exact Herdr-reported ID. `agent-session restart` is self-targeted from inside the
owned session and refuses missing resume records or supervised ownership; it is not a remote-target command. Leave
Clawde lifecycle control with its supervisor. Never use the most-recent session fallback. Refresh metadata after
creation/resume. Preserve sessions requested to persist; clean up only owned sessions otherwise.

### Bounded dispatch

Prepare a brief accessible on the target with goal, constraints, worktree, acceptance checks and artifact path. Submit
one authorized task using `a2a fleet dispatch HOST PANE_ID SESSION_ID --owner dot --task TASK_REF --request-id ID
--prompt 'Read /target/brief and implement it.' --execute`, placing the command on one shell line. Use a unique simple
correlation token. Coordinate at most two active tasks at a time; the CLI itself enforces one unresolved task per pane.

Dispatch refreshes the directory, requires exact identity, idle and readiness metadata, reserves locally, and calls
existing `a2a send` once. The sent prompt includes `[dot-fleet:ID]`; the local ledger retains intent hash and receipt.
An identical repeated ID never resubmits. A2A has no atomic expected-session-ID precondition, so use an owned target and
avoid concurrent lifecycle changes between preflight and send. A lost receipt remains uncertain and reserved.

### Results and reconciliation

Use `a2a fleet result ID` for one bounded status read. Dispatched means a task ID was returned; an exact ACK means
receipt; neither is completion. A2A completion is heuristic and becomes `reported_completed`. Inspect the artifact,
tests and session before `a2a fleet verify ID --evidence CHECKED_RESULT_REFERENCE` records completion.

A disappearing task record remains `status_unavailable` with its durable correlation and receipt. For a recovered task
ID use `a2a fleet reconcile ID --remote-task-id RECOVERED_ID --evidence RECEIPT_REFERENCE`. If the remote record is lost,
independently inspect the actual result, then use `a2a fleet reconcile ID --outcome completed --evidence RESULT_REF`.
Use outcome `failed` for proved failure or `not_submitted` only for proved non-submission; silence is not proof.

An idle composer can reject delivery, a healthy service can leave a mailbox unread, and a reachable host can have an
unresponsive watchdog. Preserve these distinctions. Never clear a draft, send extra Enter, automatically resend or
switch transport to bypass a refusal. Stop that action and report the exact target, blocker, evidence and uncertain,
pending or denied outcome. Reconcile before a new intent.

### Events and activation

Prefer the existing Herdr `events.subscribe` surface for pane lifecycle and per-pane agent-status events. These events
do not establish conversation identity by themselves: coalesce invalidations, refresh a complete snapshot, and refresh
after reconnect. Feed an existing consumer's envelope to `dot-fleet event HOST FILE --evidence SOURCE_REF` to persist
invalidation without storing event data or creating a subscription. No service is activated by this CLI. Keep on-demand refresh until integration into
an existing orchestrator is approved; alternatively attach metadata collection to the existing fifteen-minute
maintenance. Never add a duplicate timer, duplicate nightly tests, or model calls for status polling.

The deployment proposal changes only the existing A2A client package and this skill, then imports verified metadata
into an approved state directory. A long-lived collector is a separate proposal. The repository runbook at
`agent-harness/agent-to-agent-communication/client/FLEET.md` describes the format, limits and integration checks. Local
synthetic tests do not prove fleet reachability, paid-model readiness, event delivery, or deployed create/resume behavior.
