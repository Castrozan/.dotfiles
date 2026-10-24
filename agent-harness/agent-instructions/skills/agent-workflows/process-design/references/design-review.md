### Failure taxonomy walk

Walk the three categories of the multi-agent failure taxonomy against the diagram. For specification and system design,
ask whether every agent knows its task and role boundaries, whether any step can repeat without progress, whether
history survives each handoff, and whether every loop and the whole process know when to terminate.

For inter-agent misalignment, ask whether a confused agent can ask for clarification, whether a worker can derail from
its brief, whether any agent withholds information another needs, whether inputs from other agents are actually
consumed, and whether stated reasoning matches the action taken. For task verification, ask whether verification exists,
whether it checks the high-level objective rather than only low-level form, and whether it can terminate prematurely.

### Pre-mortem

Assume the process ran and failed badly, then list the most plausible reasons: wrong decomposition, a silent worker
failure, a verifier that agreed with a wrong answer, an unbounded loop, a budget overrun, a human gate nobody answered,
a watcher that never fired. Turn each reason into a concrete design change or an explicit accepted risk.

### Coupling pass

List what each step reads and writes. Steps that write the same artifact, or that depend on decisions another step makes
implicitly, are coupled and cannot run in parallel; serialize them or merge them into one step. This is the design
structure matrix idea applied to agents, and it is the main defense against parallel-writer conflicts.

### Exception matrix

For every node, confirm a handling exists for work failure, deadline, guardrail violation, and external cancellation, as
listed in the [wiring](wiring.md#failure-handling). A node whose failure has no path stalls the whole
process or fails silently; draw the failure edge or document why the failure cannot occur.

### Anti-patterns

Reject these on sight: multiple agents for sequential or tightly coupled work; parallel writers to shared state; agent
count not scaled to complexity; vague briefs that cause duplicated work or gaps; loops without an exit condition and a
cap; a verifier sharing the generator's context; decentralized coordination with no central verification; debate where
voting suffices; topology added before prompts are tuned; context dropped at handoffs or children never reporting
upward; consequential actions with no human gate; open-ended negotiating swarms.

### Evaluation plan

For a recurring process, define a small set of realistic cases, around twenty, scored by a rubric-based model judge plus
human review of the outliers, and change prompts before changing topology. For a one-off process, define the observable
done check and the live evidence that proves it instead.
