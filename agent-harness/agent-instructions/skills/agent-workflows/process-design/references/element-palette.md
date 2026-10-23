### Steps

An agent step is a model call with its own context, tools, and brief; suggest it for judgment work. A deterministic step
is a script, tool, query, or check with no model choice; prefer it whenever the predicate is exact, because it is
cheaper, repeatable, and never drifts. A read-only searcher is an agent step that reports findings and writes nothing,
the safest unit to parallelize.

A verifier checks another step's output from a clean context; prefer executable verification such as tests, builds, or
live probes over model judgment, never let it inherit the generator's reasoning, and verify where the outcome is
consumed rather than where it is written. An aggregator reduces many outputs by voting, deduplication, or ranking; a
synthesizer turns them into one answer with citations; a compressor shrinks history before a handoff so the receiver
keeps decisions without the noise.

A human gate pauses for approval, a choice, or missing facts; place one before every irreversible or owner-only action.
A watcher waits on an external condition such as a timer, a CI run, a queue, a file, or a log pattern, and wakes the
process when it changes. A sub-process is a nested reusable process with its own contract, drawn as one node at the
parent level.

### Control flow

Name control flow with the Workflow Patterns vocabulary: sequence; parallel split with synchronization; exclusive
choice; multi-choice; multiple instances with a count known only at runtime, which is the fan-out over discovered items;
and a structured loop with an exit condition and a cap.

Use the discriminator or N-of-M join when the first or the first N results suffice, paired with cancellation of the
remaining siblings. Use deferred choice when whichever event arrives first decides the path, such as a watcher racing a
worker. Use a milestone when a step may run only while the process sits in a given state. Use early exit when a cheap
step can answer and skip the expensive branch entirely.

For adaptive work whose next step depends on findings, borrow CMMN: group steps into stages, mark optional steps as
discretionary, and attach a sentry, an explicit entry or exit criterion, to each one instead of forcing a fixed order.

### Coordination strategies

A prompt chain runs steps in sequence with a gate between them. Routing classifies input and sends it to a specialized
path. Sectioning splits independent subtasks across parallel workers. Voting runs the same task several times and
aggregates; it captures most of the gain usually attributed to debate at lower cost.

Maker-checker, also called evaluator-optimizer or review-and-critique, loops a generator against an independent verifier
with a cap and a fallback. Orchestrator-workers lets a manager decompose at runtime, delegate, and integrate; the
manager maps, reduces, and manages, while workers stay narrow. Handoff transfers control so one agent is active at a
time.

A ledger manager keeps a task ledger of facts, guesses, and plan plus a progress ledger asking whether the work is done,
looping, or progressing and who acts next; it replans when progress stalls. Hierarchy adds intermediate coordinators
when one manager can no longer hold every worker's output. A blackboard posts open requests to shared state that agents
volunteer for, suited to open-ended discovery.

A staged rollout applies any bulk or irreversible step to a small canary first, verifies the outcome end to end, and
only then proceeds in throttled waves with a resumable log, pausing when a monitor reports a shared resource near its
limit and resuming when it drains. Skipping the canary turns a defect in the write path into a defect in every record.

Use debate only for multi-hop factual disputes where voting already failed. Avoid unstructured group chat in which
agents negotiate without a moderator, a turn rule, and a termination condition.

### Allocation

Allocate each step by role or by capability, never by whichever agent is free. Tier models by difficulty and add an
escalation path that sends a stuck step to a stronger model or to the human. Keep one writer per artifact; parallel
agents read, and the single writer integrates.

### State and data

Pass typed handoff artifacts with a declared shape between steps rather than free-form transcripts. Persist the plan and
progress outside any one context so a restart resumes from durable state. Declare shared state keys up front with one
owning writer per key. Mark each checkpoint where the process can resume without redoing finished work.

### Failure handling

Classify each node's failures by kind: the work fails, a deadline passes, a constraint or guardrail is violated, or an
external event cancels it. Choose one handling for each kind: retry with a cap, fall back to an alternative step,
compensate by undoing side effects, escalate, park until a signal, or cancel the whole case. Record the choice in the
node contract so failure paths appear in the diagram.
