---
block: reviewers
group: agents
provides: verdict
needs: subagents, artifact
---

### What it gives

Independent checkers, each with one lens, review a deliverable from a clean context and return MERGE or BLOCK with
findings, in a capped maker-checker loop.

### Use when

A defect would be costly, acceptance criteria exist, and a fresh context can catch what the maker cannot. Put a verifier
first whenever a test, build, or probe can decide, so reviewers judge only what code cannot.

### Instruction

Give each reviewer one lens, the artifact, and the acceptance criteria, never the maker's reasoning. Ask only for
correctness and requirement gaps, filter findings against the user's goal, return any BLOCK to the maker, and cap the
loop at two rounds with escalation to the human or a shipped quality warning as the fallback.

### Pitfalls

Model judges carry position, verbosity, and self-preference bias; reviewers asked for gaps find some even in sound work,
and chasing them all over-engineers; self-review without outside feedback can make work worse.

### Harness

Quality-assurance subagents or a workflow script with schema-typed verdicts; the `review` skill for the method; agent
team reviewers with distinct lenses.
