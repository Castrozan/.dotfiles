---
block: trigger
group: edges
provides: start
needs: none
---

### What it gives

The event that starts the process: a ticket, a webhook, a CI result, a schedule, or the human's request.

### Use when

The process recurs or must react without the human starting it. A one-off process starts from the human's request.

### Instruction

Name the trigger, the payload it carries, and the guard that ignores duplicates.

### Harness

Webhooks, CI events, cron, or a channel message routed to the driver.
