---
block: voting
group: agents
provides: verdict, artifact
needs: subagents, budget
---

### What it gives

Several independent attempts at the same task, then one picked by majority, verifier, or judge.

### Use when

Single attempts vary and a selector exists, best of all a verifier. Prefer it to debate, which at equal samples gains
less. Avoid it when the cost of several attempts outweighs the variance it removes.

### Instruction

Run the attempts with independent contexts, and diversify the briefs or models when they share priors. Select with a
verifier when one exists, by vote for reasoning tasks otherwise, and record the losing attempts' disagreements.

### Pitfalls

Cost multiplies by the attempt count; voters with shared priors agree on the same wrong answer.

### Harness

Parallel subagents or a workflow parallel step; best-of-N attempts in cloud coding agents.
