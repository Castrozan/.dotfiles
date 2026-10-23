### Task classification

Classify the task before choosing a shape. Decomposable breadth, meaning independent sub-questions or items, suits
sectioning or orchestrator-workers. Sequential, dependent reasoning suits one agent or a prompt chain. Tool-heavy work
in one shared environment suits one writing agent with read-only helpers. Open-ended discovery suits a ledger manager or
a blackboard. A quality-critical artifact suits maker-checker. Heterogeneous inputs that need different specialists suit
routing or handoff.

### Scale evidence

Controlled studies show multi-agent coordination helping strongly on decomposable tasks and hurting sharply on
sequential planning, with diminishing returns once a single agent is already strong and extra overhead on tool-heavy
work. Decentralized designs without a central verifier let errors propagate, so keep one verification point.

Multi-agent research runs consume roughly an order of magnitude more tokens than a chat, and token spend explains most
of their quality gain; adopt one only when the task's value pays for that cost. Search over agent topologies found
prompt quality outweighing topology and most topologies not helping a given task, so optimize each agent locally before
scaling the graph.

### Effort scaling

Set agent count and call budget per stage from complexity, and write the ceiling into the design. A published
calibration is one agent with a handful of tool calls for a simple fact, two to four workers for a direct comparison,
and more than ten workers with clearly divided responsibilities only for broad research. Over-spawning, duplicated work,
and endless searching are the observed failures when this rule is missing.

### Single writer

Parallel writers conflict on the implicit decisions each one makes, so keep writes single-threaded: parallelize reading,
searching, and reviewing, and let one agent integrate. When parallel writes are unavoidable, isolate each writer in its
own worktree or branch with disjoint files and add an explicit integration step with its own verifier.

### Combining patterns

Real processes combine patterns, one per stage: a router picks the path, a fan-out of read-only searchers gathers
evidence, a synthesizer reduces it, maker-checker hardens the artifact, a human gate approves the irreversible step, and
a watcher confirms the outcome live. Choose each stage's pattern from its own task class rather than imposing one
topology on the whole process.
