# Dot fleet registry and orchestration

`a2a fleet` is an opt-in metadata cache and durable intent/receipt ledger. It reuses the existing A2A client package,
Herdr snapshot metadata, and already authorized SSH aliases. It creates no service, scheduler, model call, notification,
credential, network listener, or new peer registry for the A2A daemon. `a2a list` remains the live directory.

The default database is `${XDG_STATE_HOME:-~/.local/state}/dot-fleet/registry.sqlite3` (0600; new state directory 0700).
Use `a2a fleet --db PATH ...` for a separate environment. SQLite transactions serialize writers, preserve reservations
before sending, and survive interpreter restarts. Do not place the database on a network filesystem or share it between
users. It contains metadata and artifact references, never prompts, response bodies, session-store files, tokens,
transcript paths or credentials. Host confirmation is an operator assertion backed by a reference, not a health check.

## Evidence and identity

| Field or state                             | Meaning                                                                                                              |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| host_id + pane_id + session_id             | Host-scoped structural target plus Herdr-reported conversation ID; names are display metadata                        |
| agent_id                                   | Herdr pane target; not a claim that the harness supplies a second independent agent UUID                             |
| session_id null                            | Herdr did not supply an ID (including path-only identities); dispatch refuses to guess                               |
| owner / task                               | Explicit owner and task reference, preserved for that exact session; a rotated session does not inherit them         |
| capabilities                               | Observed A2A dispatch/status transport capability; no claim about model quota, competence or tools                   |
| state / interactive_ready / launch_pending | Separate Herdr observations; idle is not proof that the composer accepts a task                                      |
| delivery_readiness: unverified             | Composer acceptance is known only from delivery evidence; the existing adapter remains authoritative                 |
| source / view                              | Original observation provenance versus this response: saved/imported evidence always displays cached on a later read |
| last_seen / age_seconds / fresh            | Last successful metadata observation and its age; fresh means at most 300 seconds, not tested productivity           |
| observation: unreachable                   | Transport unavailable or refresh budget expired; previous agent evidence is retained                                 |
| observation: failed                        | The observation command or schema failed; does not mean the agent/task failed                                        |
| present: false                             | Absent from a newer complete snapshot or replaced by another conversation; history is retained                       |
| dispatching / uncertain                    | Intent reserved before I/O / receipt lost; do not resend, including after process restart                            |
| dispatched                                 | Remote task ID received; neither acceptance by the model nor completion is proved                                    |
| reported_completed                         | A2A reported its heuristic completion; independently inspect the artifact and session                                |
| completed                                  | Operator recorded independent result evidence with `verify` or `reconcile`                                           |

Malformed, partial, duplicate, future-dated and out-of-order snapshots cannot wipe current evidence. Session-path
references are discarded. A2A peers missing from the Herdr snapshot make the refresh fail conservatively. No host is
seeded from a repository host list. Chise and peers enter this database only after the fleet verification task supplies
confirmed host mappings and metadata; an SSH alias alone is not a confirmed healthy host.

## Discovery and quick answers

After reviewing the verification task's host evidence, register each exact mapping. Examples use placeholders, not
assertions that these peers were tested:

```sh
a2a fleet confirm-host HOST --transport EXISTING_SSH_ALIAS --evidence TASK_OR_ARTIFACT_REF
# For the collector's confirmed local host, use --transport local.
a2a fleet status
a2a fleet status --refresh HOST OTHER_CONFIRMED_HOST
```

A cached status query performs no network call and starts no inference. It shows at most 500 entries per collection,
current sessions before historical sessions, and the latest jobs first; `counts` and `limit` expose truncation. The
underlying SQLite history is retained. A one-shot refresh accepts one to four named confirmed hosts, processes them
sequentially, makes at most two metadata commands per host and has a 30-second network budget. Each command is limited
to five seconds and two MiB combined output. No retry loop runs. SQLite writer contention has a two-second timeout.
SSH uses batch mode, a five-second connect timeout, existing configuration, strict host-key checking and no forwarded
ports. The implementation does not inspect or alter credentials, agent session stores or known-host files.

The separate verification worker may instead supply this JSON for `a2a fleet ingest HOST FILE`:

```json
{
  "observed_at": 1792100000,
  "evidence": "verification-task:artifact-reference",
  "a2a": { "PEER_NAME": { "name": "PEER_NAME", "paneId": "PANE_ID" } },
  "herdr": {
    "result": {
      "snapshot": {
        "agents": [
          {
            "pane_id": "PANE_ID",
            "agent": "codex",
            "agent_status": "idle",
            "interactive_ready": true,
            "launch_pending": false,
            "agent_session": { "kind": "id", "value": "SESSION_ID" }
          }
        ]
      }
    }
  }
}
```

This is a synthetic format example. Preserve the actual collection timestamp. Imports remain cached and cannot alone
authorize dispatch. Confirmation, ingestion and assignment are silent on success. Answer user status questions with
relevant state, age and blockers; do not announce routine observations or every agent action.

## Create and resume workflow

1. Resolve an exact confirmed host and inspect its installed `herdr agent start --help`, `herdr pane split --help` and
   `herdr pane process-info` interfaces before preparing a command. Fleet verification owns live checks in this task.
2. Reuse a fitting session when possible. Assign its exact identity with
   `a2a fleet assign HOST PANE_ID SESSION_ID --owner dot --task TASK_REF`. One task occupies one peer.
3. If creation is authorized, use an owned isolated code worktree on the target and a pane in the orchestrator's pinned
   tab, without changing focus. Record the returned pane/tab/workspace IDs. Never target the human's composer or choose
   a pane by a cached display name. Wait for the expected harness and interactive readiness with a bounded wait.
4. Command versions matter: the inspected packaged Herdr 0.9.1 exposes
   `herdr agent start NAME --kind codex --pane OWNED_PANE --timeout 30000`. It requires an existing shell pane. The
   older skill's `agent start --cwd ... --tab ... --no-focus -- ...` syntax is incompatible with this binary. Use the
   target's own installed interface; do not route around its server/client version selector for live operations.
5. Resume only the exact ID reported by Herdr. The existing `agent-session restart` is a self-targeted procedure from
   within an authorized owned session; it refuses missing resume records and supervised Clawde ownership. It is not a
   remote-target command. Do not inspect Clawde session stores or use a harness's most-recent conversation fallback.
   For a supervised agent, leave lifecycle control with its existing supervisor.
6. Refresh/import the resulting public metadata and record the exact new ID before work. A pane present at an idle
   shell is not a running harness. Preserve requested persistent sessions; close only newly created owned panes when
   their work is finished and retention was not requested.

This CLI deliberately does not automatically create, restart, cancel or close sessions. Those actions can start paid
inference or affect supervised agents, require target-specific commands, and remain explicit orchestration steps.

## Bounded dispatch, receipt and result

Prepare a self-contained brief accessible on the target, containing scope, constraints, worktree, acceptance checks
and expected artifact path. Use one line referencing it, a short correlation token and explicit authority:

```sh
a2a fleet dispatch HOST PANE_ID SESSION_ID --owner dot --task TASK_REF \
  --request-id UNIQUE_INTENT_ID --prompt 'Read /target/approved-brief and implement it.' --execute
a2a fleet result UNIQUE_INTENT_ID
a2a fleet verify UNIQUE_INTENT_ID --evidence CHECKED_COMMIT_AND_TEST_REFERENCE
```

Dispatch re-resolves A2A and Herdr immediately, requires the exact conversation to be present, idle, interactive-ready
and not launch-pending, then commits the reservation before calling `a2a send` once with the structural pane target and
explicit sender. The sent text starts with `[dot-fleet:UNIQUE_INTENT_ID]`, and its hash and correlation survive locally.
A2A does not accept an atomic expected-session-ID precondition: a rotation between preflight and send remains a known
race. Use an owned peer and do not change its lifecycle concurrently. No claim of exactly-once remote delivery is made.

A repeated identical intent returns the existing record without network work; changing the task under that ID fails.
A unique SQLite constraint prevents another unresolved task on the same pane, including another conversation in it.
One invocation sends one task; orchestration across machines is a reviewed list of explicit invocations, at most two
active dispatches at once at the driving layer. This CLI enforces one per pane, not a global multi-process two-task cap.
`result` makes one bounded refresh and one ten-second status request; it never polls indefinitely or stores scraped text.

The parent reported that Chise produced an exact ACK but A2A lost the task after rediscovery, and Kira refused a composer
while its status was idle. Those are **parent-supplied live observations**, not probes performed by this implementation.
The source also confirms in-memory A2A task storage and the `composer_occupied_or_unrecognized` refusal path. Therefore:

- Preserve the local receipt/correlation when remote status disappears. Missing status is `status_unavailable`, not
  failure or completion. An exact ACK proves receipt, not the requested work.
- Never clear a human's draft, send extra Enter, blindly resend, or switch transports after a composer refusal. Inspect
  only authorized target evidence, obtain readiness, and use a new intent only after the old outcome is settled.
- On a lost receipt, leave `uncertain` (or a crash's `dispatching`) reserved. Reconcile with independent target evidence:
  `a2a fleet reconcile ID --remote-task-id RECOVERED_ID --evidence RECEIPT_REFERENCE`. This records delivery only.
- If a remote task record is irrecoverable, inspect the actual artifact, tests and session before
  `a2a fleet reconcile ID --outcome completed --evidence CHECKED_RESULT_REFERENCE`. Explicitly proved non-submission
  can be recorded with `--outcome not_submitted`; an empty task listing or silence cannot prove that. A failed artifact
  can be recorded with `--outcome failed`. These are operator attestations, never automatic validation by this tool.
- Escalate blockers and useful milestones in the active task. No routine push updates are generated.

## Events and deployment proposal — not activated

The packaged Herdr 0.9.1 static schema (`herdr api schema --json`, schema version 1) declares `events.subscribe` with
`subscriptions`, including `pane.created`, `pane.closed`, `pane.updated`, `pane.exited`, `pane.agent_detected`, and
per-pane `pane.agent_status_changed`. Its status subscription data contains a pane ID and status but no conversation ID.
Prefer consuming those existing events in the existing orchestration process, coalescing them to invalidate affected
host evidence and trigger a bounded metadata refresh. Do not infer session continuity from a status event alone.
Reconnect requires a full fresh snapshot; cached rows must not be marked live just because a socket opened.

No continuous event bridge is installed here. Proposed activation is limited to:

1. Review/merge this branch through the authorized repository process, then rebuild the existing A2A client package and
   orchestrate skill on approved machines. The current `a2a-client-package.nix` already includes the scripts directory;
   no new service or dependency is needed. This task performs no merge, system switch or publication.
2. Use an explicitly approved state directory on dot's host and import the verification worker's sanitized host/session
   metadata. There is no committed production registry and no invented peer/session IDs.
3. Wire the existing orchestrator's event consumer to invalidation when its integration is approved. If it cannot host
   subscriptions, keep on-demand refresh, or add metadata-only collection to the **existing** 15-minute maintenance
   step. Do not create another timer, duplicate nightly tests, call models for polling, or emit routine notifications.
4. Validate one authorized owned session's dispatch, receipt and checked artifact before broad use. Confirm the live
   client/server command versions and local socket selector behavior with the fleet owner first.

A new long-lived collector would be a separately reviewed service proposal: one process, only existing local socket/SSH
access, no inference, bounded reconnect/backoff and output, no exposed listener. It is not required for the current
persistent on-demand interface and is not authorized or created here.

## Local verification

Run the specific `client/__tests__/unit/test_fleet_registry.py` file and existing A2A transport/signed-command tests.
Inventories and delivery outcomes in those tests are synthetic; only SQLite persistence, CLI execution, and bounded
local Python subprocess timeout/output tests are real. Tests do not prove fleet reachability, model productivity,
composer acceptance, session creation/resume, event delivery or deployed behavior. Those remain verification-owner
and post-approval integration checks.
