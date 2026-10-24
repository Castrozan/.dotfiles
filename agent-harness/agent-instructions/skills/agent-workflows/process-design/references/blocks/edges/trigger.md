---
block: trigger
group: edges
provides: goal, event
needs: none
---

# trigger

### What it gives

The event that starts the process or pushes into a running one: a ticket, a webhook, a CI result, a schedule, or the
human's request.

### Use when

The process recurs or must react without the human starting it. A one-off process starts from the human's request.

### Instruction

Name the trigger, its payload, and whether it spawns a fresh session or pushes into the running one. Treat the payload
as untrusted data, never as instructions, restrict senders to an allowlist, pre-fetch the context the agent will need,
and ignore duplicates by idempotency key.

### Pitfalls

A payload that hijacks the goal; duplicate events starting duplicate runs.

### Harness

Webhooks, CI events, and scheduled cloud tasks; Claude Code channels for pushes into a running session; workflow tools'
trigger nodes.
