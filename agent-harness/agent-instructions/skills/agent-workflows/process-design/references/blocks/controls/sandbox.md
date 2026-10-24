---
block: sandbox
group: controls
provides: containment
needs: driver
---

### What it gives

Filesystem and network isolation that lets the agent act autonomously without an approval prompt per action, and
contains it when it misbehaves.

### Use when

The agent runs code, runs unattended, or would otherwise ask for routine approvals. Isolate both filesystem and network:
without the first it escapes, and without the second it can exfiltrate credentials.

### Instruction

Allowlist the directories and hosts the process needs and nothing else, keep secrets outside the sandbox and inject them
only into the scripts that need them, and grant least privilege per block.

### Pitfalls

An allowlist widened mid-run to unblock a step; secrets readable from inside the sandbox.

### Harness

Claude Code's built-in sandbox, dev containers, or virtual machines; Codex sandbox modes, which subagents inherit.
