---
block: reviewers
group: agents
provides: verdict
needs: subagents
---

### What it gives

Independent checkers, each with one lens, review a deliverable from a clean context and return MERGE or BLOCK with
findings, in a capped maker-checker loop.

### Use when

A defect would be costly and a fresh context can catch what the maker cannot. Prefer an executable check, such as a
test, build, or live probe, whenever one can decide.

### Instruction

Give each reviewer one lens and no access to the maker's reasoning. Any BLOCK returns the work to the maker; cap the
loop at two rounds and escalate a third BLOCK to the human. Verify where the outcome is consumed, not where it is
written.

### Harness

Quality-assurance subagents or a workflow script with schema-typed verdicts; the `review` skill for the method.
