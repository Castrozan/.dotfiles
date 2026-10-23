### Source format

Use Mermaid as the single diagram source: GitHub, Obsidian, and most documentation and artifact surfaces render it
natively, agent frameworks export it, and models write it reliably. Keep the Mermaid text in the persisted design; every
other view derives from it. Start from the [legend](../assets/legend.mmd), which shows every convention below in one
small investigation process.

### Flowchart conventions

Use `flowchart` with one `subgraph` lane per actor: the main agent, background workers, watchers, and the human. Give
each palette element one shape: stadium `(["..."])` for start and end, rounded `("...")` for agent steps, rectangle
`["..."]` for deterministic steps, rhombus `{"..."}` for routers, circle `(("..."))` for splits and joins, hexagon
`{{"..."}}` for human gates, asymmetric `>"..."]` for watchers, cylinder `[("...")]` for persisted state, and subroutine
`[["..."]]` for sub-processes.

Draw control flow as `-->`, conditional branches as `-->|"condition"|`, failure and escalation paths as dashed `-.->`,
loop-backs as thick `==>` labeled with their cap, and reads or writes of persisted state as `--o`. Label every join with
its completion rule and every fan-out with its count rule. Color roles with `classDef`, keeping verifiers visibly
distinct from generators.

Stay on the classic shape syntax shown here; newer extended shape forms render in fewer places. Split a diagram that
outgrows one screen into a top-level process with sub-process nodes, each expanded in its own diagram.

### Sequence diagrams

Add a `sequenceDiagram` when timing, messaging, or concurrency matters more than topology. Map fan-out to `par`, bounded
loops to `loop` with the cap in the label, routing to `alt`, optional steps to `opt`, and must-not-interrupt sections
such as irreversible actions to `critical`.

### Terminal view

When the reader sees only a terminal, also write the process as a Unicode box-drawing outline with the same lanes,
labels, caps, and join rules, so it reads without any renderer and diffs cleanly. Terminal Mermaid renderers parse only
a subset: shapes beyond plain boxes and `class` styling lines print as literal text or phantom nodes, and `stateDiagram`
is mostly unsupported, so never present a terminal render as the diagram without checking it.

### Rich view

When the harness offers a rendered surface such as an artifact, a document, a pull request, or a note, publish the
Mermaid there for the human and keep the terminal outline in the conversation. For dense graphs where Mermaid layout
breaks down, emit Graphviz DOT as an alternate view, never as the source of truth.
