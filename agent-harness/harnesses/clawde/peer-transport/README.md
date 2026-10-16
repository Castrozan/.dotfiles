# Notification delivery and uncertain outcomes

`a2a notify` posts a distinct notification ID to a pane's process-local mailbox. The observation loop delivers pending
messages only after the existing busy/blocked/composer checks allow input. Messages are batched to 32 KiB and the mailbox
holds at most 64 unread messages, including quarantined ones. No content-based deduplication suppresses legitimate new
messages with the same text.

Before an input attempt, the mailbox atomically claims the exact IDs and marks their `deliveryState` as `uncertain`.
Only a definite refusal before any input-producing command restores `pending`. A successful delivery removes those IDs.
A timeout, lost acknowledgment, unexpected exception or interrupted worker leaves the IDs quarantined and visible through
`a2a inbox`; subsequent observation passes cannot automatically submit them again. Concurrent workers cannot claim the
same batch, and session/delivery-object reconstruction during fleet reconciliation preserves the shared mailbox state.

`HerdrPromptAdapter` distinguishes its read-only preflight refusal (`PromptNotSubmitted`) from an error returned after
invoking `herdr agent prompt`. Herdr can accept input before its wait reports timeout or `agent_prompt_stalled`, so a
nonzero result from that command does not establish non-submission. Explicit task HTTP statuses and occupied-input guards
retain their existing behavior; this fix changes automatic notification retry only.

## Explicit recovery

Read `a2a inbox PANE_ID` and correlate the exact ID with independently checked recipient evidence. An uncertain message
may have been delivered, may still be in the composer, or may not have reached it. Do not infer the outcome from an idle
pane, a timeout, an empty history or a missing task record. Do not clear a draft, add Enter, or switch transports.

After independently confirming delivery, use `a2a ack PANE_ID MESSAGE_ID` to remove only that message from the mailbox.
Acknowledgment is idempotent and sends no input. If independent evidence proves non-submission, acknowledge the old ID
and issue a new notification only when that new send is authorized. There is no automatic retry/reset endpoint for an
uncertain message. Distinct pending messages remain eligible for ordinary readiness checks.

Mailboxes remain process-local, as before this fix. A whole daemon restart loses both pending and uncertain entries;
it does not recover or replay them. Missing entries after restart are not evidence of non-delivery and must never cause
automatic reposting. Preserve operator-relevant receipts before an approved deployment restart. Do not restart the daemon
to clear uncertainty. This hotfix adds no durable message-body store or new credential/session access.

## Verification and deployment boundary

The packaged transport check includes causal accepted-then-ACK-error tests for Codex, Claude and OpenCode, native-prompt
timeout, worker interruption/restart, rename/reconciliation, exact-ID acknowledgment, distinct messages and atomic claims.
These use fake peers and temporary test HTTP servers; they do not contact production sessions. The original behavior
replayed one notification three times in three passes; the fixed behavior submits it once and exposes uncertainty.

The fleet/deployment owner integrates the tested commit and verifies the configured/running A2A source path through its
normal deployment workflow. No Herdr restart, pane/tab mutation, harness interruption or test prompt is needed for this
code change. Keep deployment separate from live incident attribution: the defect is reproduced, while B11/Orion message
and sender attribution remain unverified. Preserve the user's resumed B11 and edited history.
