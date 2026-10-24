---
block: solo-loop
group: agents
provides: driver, artifact
needs: goal, budget
---

# solo-loop

### What it gives

One agent with tools does the whole task in a continuous loop of acting, observing, and deciding, with no helpers and no
handoffs. Every decision stays in one context, which removes coordination failures entirely.

### Use when

The work is sequential, its edits depend on each other, or it is coding with few truly parallel parts; this is the
default agent block. Avoid it when the context overflows even with compaction, or when wide read-heavy discovery would
run faster as parallel scouts.

### Instruction

Work the task end to end yourself. Recite the goal by rewriting the todo list as you go, keep failed attempts visible
instead of erasing them, and compact deliberately before the context fills. Gate the stop on a check you can run; after
two failed corrections, restart with a better brief instead of pushing on.

### Pitfalls

Context rot as the window fills, goal drift over long runs, unscoped exploration that never converges, and declaring
victory before the done check passes.

### Harness

Any harness's main session; Claude Code adds goal evaluation, self-paced loops, and focused compaction. For runs longer
than one sitting, pair it with a scheduled wakeup and a tracker.
