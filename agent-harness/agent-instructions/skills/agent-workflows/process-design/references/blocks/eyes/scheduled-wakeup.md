---
block: scheduled-wakeup
group: eyes
provides: event
needs: driver, state
---

# scheduled-wakeup

### What it gives

A recurring wakeup that brings the driver back on a schedule for processes that run hours or days.

### Use when

The process outlives one sitting or waits on slow external state and approximate timing is fine; exact-time jobs belong
in cron. Avoid it for short in-session checks, where a short loop fits.

### Instruction

Keep a short checklist the driver rereads on every wakeup, read the tracker first, act on what changed, record the
result, answer an explicit no-op when nothing did, and schedule the next wakeup or stop. Use a durable scheduler when
the run must survive the session.

### Pitfalls

Session-scoped schedules die with the session; a wakeup without a tracker has no memory of what it already checked.

### Harness

Claude Code scheduled tasks and wakeups; cloud scheduled tasks for unattended runs; supervised agent heartbeats.
