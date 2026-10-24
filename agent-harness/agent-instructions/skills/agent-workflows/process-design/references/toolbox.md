### Blocks

A process is a composition of capability blocks picked from this toolbox. Each block lives in its own file whose
frontmatter names its group, the ports it provides, and the ports it needs, and whose body says what it gives, when to
use it, the instruction the composed process carries, and how each harness implements it. Name a composition by its
blocks, such as main and helpers with skill and script, script monitor, monitor subagents, canary and waves, and
tracker.

### Ports

A `driver` is the agent that owns the process loop and every side effect; `subagents` is its ability to spawn helpers; a
`peer` is another main agent reachable by messages. An `action` is a deterministic capability, and an `observable` is a
status the process can read, such as a log, a query, or a status command. An `alarm` is an event fired when an
observable crosses a threshold; a `watch` acts on observables or alarms; a `wakeup` brings the driver back on a
schedule.

An `approval` is the owner's recorded yes; a `policy` is a deterministic block; `state` is durable process memory;
`isolation` is a separate checkout per writer. A `start` begins the process and an `outcome` reports it. The `findings`,
`verdict`, `rollout`, and `rehearsal` ports are the outputs of scouts, reviewers, canary and waves, and dry run.

### Composition rules

A composition is valid when: 1) every needed port is provided by a block in it; 2) it has exactly one driver, and every
peer is its own nested composition with its own driver; 3) every artifact has one writer, so only the driver runs side
effects and writes the tracker while helpers read, unless a worktree isolates them; 4) every irreversible action and
every outward report passes an approval; 5) every alarm reaches the driver; 6) zero-token blocks come first, so a script
monitor precedes agent eyes and a hand precedes an agent step; 7) agent blocks climb from solo loop only as far as
[topology selection](topology-selection.md) evidence forces.

### Changing a composition

When the human reframes the goal, change the composition by adding, removing, or swapping named blocks, and say which
block changed and why before redrawing. Add a new block only when no block fits and an existing block cannot be
extended; give it ports from this vocabulary and a file of its own. Wire blocks with the control-flow, state, and
failure names in [wiring](wiring.md).
