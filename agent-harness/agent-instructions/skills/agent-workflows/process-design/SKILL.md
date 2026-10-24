---
name: process-design
description: "Co-design multi-step, multi-agent processes by composing capability blocks from a toolbox (agents, deterministic tools, monitors, gates, memory), redrawing with the human each round, then suggesting a dry run. Use before orchestrating complex agent work."
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

Run the design as this loop with the human: 1) the human frames the goal; 2) propose the smallest composition of toolbox
blocks that fits it, naming the nearest alternative composition and why it lost; 3) draw it; 4) the human reframes the
goal, and you propose the block change and redraw, repeating until the human is satisfied; 5) draw the final composition
with every block's contract; 6) suggest a dry run before the first real action.

Turn each framing into the outcome, the done check, constraints, the budget in tokens, time, and agents, and every
irreversible or owner-only action; ask one question at a time, only for forks evidence cannot settle. When acting
autonomously, run the same loop alone and record the evidence behind each change of composition.

### Argue it down first

Climb the complexity ladder only as far as evidence forces: a deterministic script, one model call, one agent with
tools, a fixed workflow, then multiple agents. Multi-agent designs win on decomposable breadth, lose on sequential,
tightly coupled, or tool-heavy work, and multiply token cost; tune a single agent's brief before adding topology. Read
[topology selection](references/topology-selection.md) to classify the task and pick the shape.

### Compose from the toolbox

Build every process from capability blocks, one file each, and load only the blocks a proposal uses. Read
[toolbox](references/toolbox.md) for ports, composition rules, and how a composition changes, and
[wiring](references/wiring.md) for the control-flow, state, and failure names that connect blocks.

Agents decide who thinks: [solo loop](references/blocks/solo-loop.md), [main and
helpers](references/blocks/main-and-helpers.md), [delegator](references/blocks/delegator.md),
[orchestrator](references/blocks/orchestrator.md), [scouts](references/blocks/scouts.md),
[reviewers](references/blocks/reviewers.md), and [peer session](references/blocks/peer-session.md).

Hands perform deterministic actions: [skill and script](references/blocks/skill-and-script.md), [workflow
script](references/blocks/workflow-script.md), and [MCP server](references/blocks/mcp-server.md). Eyes watch the running
process: [main short loop](references/blocks/main-short-loop.md), [monitor
subagents](references/blocks/monitor-subagents.md), [script monitor](references/blocks/script-monitor.md), and
[heartbeat](references/blocks/heartbeat.md).

Controls bound risk: [human gate](references/blocks/human-gate.md), [guardrail
hook](references/blocks/guardrail-hook.md), [canary and waves](references/blocks/canary-and-waves.md), and [dry
run](references/blocks/dry-run.md). Memory persists and isolates: [tracker](references/blocks/tracker.md), and
[worktree](references/blocks/worktree.md). Edges start and finish the process: [trigger](references/blocks/trigger.md),
and [report](references/blocks/report.md).

### Specify node contracts

Give every agent block a delegation brief: objective, inputs, output shape, allowed capabilities, effort budget, and
stop condition. Give every node and loop a failure path and a checkpoint, every join its completion rule, every fan-out
its count rule and ceiling, and every watcher its signals, baseline of known noise, thresholds, cadence, and exit. A
node missing any of these is incomplete, not something to decide at runtime or to patch with follow-up messages.

### Critique before running

Run [design review](references/design-review.md) on the composition before its final drawing: the failure taxonomy walk,
a pre-mortem, a coupling pass for parallel writers, the exception matrix, and the anti-pattern list. Fix findings in the
design and redraw it.

### Visualize

Draw per [visualization](references/visualization.md): a Mermaid flowchart with gates inline and lanes only for
concurrent actors as the source of truth, a sequence diagram when timing or messaging matters, and a Unicode C4 dynamic
view wherever only a terminal shows it. Show the diagram at every iteration, not only at the end.

### Map to the harness

Translate the approved design through [harness mapping](references/harness-mapping.md) into the mechanics of the runtime
that will execute it, naming every element that runtime cannot express and the substitute chosen. Hand script workflows
to the harness's workflow authoring skill, cross-session peers to the `orchestrate` skill, and autonomous runs to the
`goal-prompt` skill.

### Keep the diagram a contract

Persist the design beside its executable form, in the task's deep-work workspace or the repository's equivalent. After
each run, compare what executed (agents spawned, loops taken, failures hit, gates crossed) against the diagram and
revise the design when they diverge, so the executable never drifts silently away from the approved process.

When the process already ran by hand, run the same comparison backwards: draw the as-run diagram from its transcript and
tracker first, then design against it, so every divergence names a concrete failure the new design prevents.

### Sources

For the literature and community practice behind each element and check, read [sources](references/sources.md).
