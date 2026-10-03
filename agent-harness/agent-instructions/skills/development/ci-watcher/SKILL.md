---
name: ci-watcher
description: Wait for hosted CI results without repeated agent polling. Use after a push or when asked to watch a run and collect its failures.
---

### Execution

Use `ci-watcher --help` for the runnable interface. Start one invocation for each required run through the harness's
background execution facility, then continue independent work or yield until completion. The watcher owns polling;
reading its log repeatedly recreates the model loop it replaces.

Resolve the target with the [forge skill](../forge/SKILL.md); numeric run identifiers are scoped to their hosting
provider and repository. An explicit repository URL prevents a default CLI host from selecting another account.

### Result

Read the returned verdict and retained logs before deciding whether fixes are needed. A watcher error or timeout is not
a CI verdict. A completed run covers only that run and attempt; other required workflows retain their own verdicts.

### Authority

Watching does not authorize rerunning, cancelling, or changing CI. Stopping the watcher leaves the remote run intact.
