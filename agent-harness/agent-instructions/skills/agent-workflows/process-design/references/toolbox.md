### Blocks

A process is a composition of capability blocks picked from this toolbox. Each block lives in its own file whose
frontmatter names its group, the ports it provides, and the ports it needs, and whose body says what it gives, when to
use it, the instruction the composed process carries, its pitfalls, and how each harness implements it. Name a
composition by its blocks, such as main and helpers with skill and script, script monitor, canary and waves, budget, and
tracker.

Every agent block also carries two attributes: a model tier chosen by the difficulty of its role, and its share of the
budget. The [consultant](blocks/agents/consultant.md) block owns the tiering rule.

### Ports

Structure ports: a `driver` is the agent that owns the process loop and every side effect; `subagents` is its ability to
spawn helpers; a `peer` is another main agent reachable by messages. Data ports: a `goal` is the objective with
acceptance criteria, which the human's framing always provides; a `brief` is a delegation prompt; an `artifact` is a
reference to a produced file, change, or record, never its raw content; a `finding` is condensed read-only evidence; a
`verdict` is pass or fail, or MERGE or BLOCK, with reasons; a `handoff` is a phase summary; `state` is durable process
memory; a `trace` is a record of what ran.

Capability ports: an `action` is a deterministic capability; an `observable` is a status the process can read, which an
external system's own status command or dashboard also provides; an `event` is a wake signal; a `watch` acts on
observables or events; an `approval` is a recorded yes that only a human can give; a `policy` is a deterministic block;
a `budget` is a set of ceilings; `isolation` and `containment` separate writers from each other and the process from
the machine. The `rollout`, `rehearsal`, and `outcome` ports are the products of canary and waves, dry run, and report.

### Composition rules

A composition is valid when: 1) every needed port is provided by a block in it; 2) it has exactly one driver, and every
peer is its own nested composition with its own driver; 3) every artifact has one writer, so only the driver runs side
effects and writes the tracker while helpers read, and parallel writers each get isolation; 4) every irreversible action
and every outward report passes an approval, and no agent relays one on a human's behalf.

It also needs: 5) every event reaches the driver; 6) every loop passes through a budget whose fallback ends in a human
gate or a report; 7) a verifier precedes reviewers, waves, and reports wherever an executable check exists, and
reviewers never share the producer's context; 8) agents exchange artifacts and findings, never raw dumps; 9) zero-token
blocks come first, so a script monitor precedes agent eyes and a hand precedes an agent step.

Start from solo loop, verifier, and budget, and make every added block name the failure it prevents; agent blocks climb
only as far as [topology selection](topology-selection.md) evidence forces.

### Changing a composition

When the human reframes the goal, change the composition by adding, removing, or swapping named blocks, and say which
block changed and why before redrawing. Add a new block only when no block fits and an existing block cannot be
extended; give it ports from this vocabulary and a file of its own. Wire blocks with the control-flow, state, and
failure names in [wiring](wiring.md).
