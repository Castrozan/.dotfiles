---
block: scheduled-wakeup
group: eyes
provides: wakeup
needs: driver
---

### What it gives

A recurring wakeup that brings the driver back on a schedule for processes that run hours or days.

### Use when

The process outlives one sitting or waits on slow external state. Avoid short intervals that poll what a monitor could
announce.

### Instruction

On each wakeup, read the tracker first, act on what changed, record the result, and schedule the next wakeup or stop.

### Harness

Scheduled wakeups, cron, or a supervised agent heartbeat.
