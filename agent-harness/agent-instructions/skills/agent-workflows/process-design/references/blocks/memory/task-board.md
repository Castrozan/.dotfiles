---
block: task-board
group: memory
provides: brief, state
needs: driver
---

### What it gives

A shared list of tasks with dependencies that several agents claim under a lock, as opposed to the tracker's single
writer.

### Use when

Many peers or teammates pull work in parallel and dependencies decide what is ready. Avoid it with one worker, where the
tracker is enough.

### Instruction

Give each task an identifier that cannot collide, its dependencies, and a claim lock; let an agent claim only ready
tasks, release a claim it cannot finish, and keep task status current so dependents unblock.

### Pitfalls

Lagging status blocks dependents; several agents fixing the same bug overwrite each other.

### Harness

Claude Code agent teams' shared task list with file-locked claims; lock files in a shared repository; dependency-aware
trackers.
