---
block: solo-loop
group: agents
provides: driver
needs: none
---

### What it gives

One agent with tools does the whole task in a continuous loop of acting, observing, and deciding, with no helpers and no
handoffs. It keeps every decision in one context, which removes coordination failures entirely.

### Use when

The work is sequential, tightly coupled, or tool heavy, or a single context can hold it. Start here and climb to another
agent block only when evidence shows breadth that parallelizes or a context that overflows.

### Instruction

Work the task end to end yourself. Persist decisions in the tracker when the task can outlive the context. Stop at the
done check, at a gate, or at the budget, and report which one ended the run.

### Harness

Any harness's main session. For runs longer than one sitting, pair it with a heartbeat and a tracker so a restart
resumes from durable state.
