### Mapping rule

Map each block and wiring element to the narrowest mechanism the target runtime offers, and keep control flow in the
main agent whenever the runtime has no mechanism for it. Check the runtime's current documentation for concurrency caps,
background behavior, and feature status before committing to a mapping, because these change between releases.

### Claude Code

Agent steps and read-only searchers map to subagents, which run with a fresh context and can run in the background;
continue a stateful worker by messaging it rather than respawning it. A fixed-shape fan-out, pipeline, or maker-checker
loop maps to a workflow script with schema-typed outputs, which can resume. A started workflow accepts no human input,
so split the design at every human gate into separate workflow runs, with the gate held by the main agent.

Human gates map to a structured question to the user. Watchers map to background shell commands, monitors, and scheduled
wakeups. A watcher subagent that polls on its own spends model tokens on every quiet check, so prefer a deterministic
monitor that emits the event plus a subagent the main agent messages or spawns to diagnose it. Guardrails and
deterministic gates map to hooks and permission rules. Parallel writers map to isolated worktrees. A shared task list
with dependencies maps to agent teams where that feature is enabled.

### Codex and OpenCode

Codex spawns subagents when the brief or an instruction asks for them, supports custom agent definitions, and caps
concurrent threads per session; it has no workflow script runner, so the main agent executes joins, loops, and gates
itself. OpenCode delegates to subagents through its task tool from a primary agent and likewise leaves control flow to
that primary agent.

### Cross-session peers

When workers must be long-lived interactive sessions, live on another harness, or run on another machine, map them to
peers through the `orchestrate` skill; the main agent then becomes a ledger manager that dispatches, observes, and
corrects them.

### Agent frameworks

When the process will ship as software rather than as an agent session, map it onto the framework's own vocabulary.
LangGraph offers state with reducers, nodes, conditional edges, `Send` for fan-out, `interrupt` for human gates, and
checkpointers. CrewAI Flows offer start, listen, router, and join decorators with persistence and human feedback.
Microsoft Agent Framework offers executors, fan-out and fan-in edges, human request and response, checkpoints, and
built-in sequential, concurrent, handoff, group chat, and Magentic orchestrations.

The OpenAI Agents SDK offers handoffs, agents as tools, and guardrails. Google ADK offers sequential, parallel, and loop
agents. Temporal offers durable workflows whose activities carry retry policies, with signals, updates, timers, and
child workflows; use it when the process must survive restarts over hours or days.
