---
block: peer-session
group: agents
provides: peer
needs: none
---

### What it gives

A long-lived interactive session in its own visible terminal pane, which the human can watch and talk to, instead of a
hidden subagent.

### Use when

A worker must outlive the main context, run on another harness or machine, or stay visible for the human to steer. Avoid
it for short tasks a subagent finishes.

### Instruction

Start the peer with its own goal and composition, name it, and address it by name. Read its pane or transcript before
messaging it, and never type into a pane the human is using.

### Harness

Herdr panes through the `orchestrate` skill; any harness that keeps a resumable session.
