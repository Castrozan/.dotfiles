---
name: process-design
description: "Co-design multi-step, multi-agent processes or workflows from an established element palette: topology, node contracts, failure-taxonomy critique, Mermaid diagrams, harness mapping. Use before orchestrating complex agent work."
---

### Core authority

Core [delegation](../../../core-rules/core.md#delegation), [evidence](../../../core-rules/core.md#evidence), and
[autonomy](../../../core-rules/core.md#autonomy) own who decides, how candidates are judged, and when to ask. This skill
owns the bounded procedure for designing a process before anything executes; the `deliver` skill uses it for its build
process, and execution belongs to the harness's workflow, subagent, and orchestration skills.

### Scope

Use this when work needs several agents, strategies, or phases whose order, parallelism, verification, and failure
handling are not obvious: an investigation that fans out, a migration, a recurring pipeline, a review swarm. The output
is a design made of a diagram, one contract per node, and a record of each decided fork; never execute from this skill.
When one agent finishes the task in one pass, say so and stop.

### Co-design loop

Run the design as a conversation with the human, or as the same loop alone when acting autonomously: 1) fix the outcome,
the done check, constraints, the budget in tokens, time, and agents, and every irreversible or owner-only action; 2) ask
one question at a time, only for forks evidence cannot settle; 3) produce two or three candidates with different
topologies and recommend one with its tradeoff; 4) iterate on the chosen diagram and contracts; 5) get approval before
any execution starts.

Do not drop the alternative candidates because the first idea looks adequate: comparing topologies is where most of the
design value appears, and a lone candidate hides its own cost.

### Argue it down first

Climb the complexity ladder only as far as evidence forces: a deterministic script, one model call, one agent with
tools, a fixed workflow, then multiple agents. Multi-agent designs win on decomposable breadth, lose on sequential,
tightly coupled, or tool-heavy work, and multiply token cost; tune a single agent's brief before adding topology. Read
[topology selection](references/topology-selection.md) to classify the task and pick the shape.

### Compose from the palette

Build every process from the named elements in [element palette](references/element-palette.md): steps, control-flow
patterns, coordination strategies, allocation, state, and failure handling. Use their established names so the design
maps onto any framework or harness. Add a new element only when no palette element fits, and name the ones rejected.

### Specify node contracts

Give every agent node a delegation brief: objective, inputs, output shape, allowed capabilities, effort budget, and stop
condition. Give every node and loop a failure path and a checkpoint, every join its completion rule, and every fan-out
its count rule and ceiling. A node missing any of these is incomplete, not something to decide at runtime.

### Critique before running

Run [design review](references/design-review.md) on the recommended design: the failure taxonomy walk, a pre-mortem, a
coupling pass for parallel writers, the exception matrix, and the anti-pattern list. Fix findings in the design and
redraw it before approval.

### Visualize

Draw per [visualization](references/visualization.md): a Mermaid flowchart with one lane per actor as the source of
truth, a sequence diagram when timing or messaging matters, and a Unicode outline wherever only a terminal shows it.
Show the diagram at every iteration, not only at the end.

### Map to the harness

Translate the approved design through [harness mapping](references/harness-mapping.md) into the mechanics of the runtime
that will execute it, naming every element that runtime cannot express and the substitute chosen. Hand script workflows
to the harness's workflow authoring skill, cross-session peers to the `orchestrate` skill, and autonomous runs to the
`goal-prompt` skill.

### Keep the diagram a contract

Persist the design beside its executable form, in the task's deep-work workspace or the repository's equivalent. After
each run, compare what executed (agents spawned, loops taken, failures hit, gates crossed) against the diagram and
revise the design when they diverge, so the executable never drifts silently away from the approved process.

### Sources

For the literature and community practice behind each element and check, read [sources](references/sources.md).
