<budget-the-control-flow>
Treat each agent or model call as budgeted delegation. Before approving a workflow, derive its minimum and maximum call
counts from the control flow, including retries, gates, synthesis, and calls made for each item or finding. A workflow
does not become cheap because its calls run in parallel or happen behind one tool invocation.
</budget-the-control-flow>

<routine-workflows>
Keep a mandatory or routine workflow at two model calls or fewer unless the owner explicitly accepts a larger fixed
budget. Never launch one call per review dimension; let one reviewer apply all related lenses, then batch all candidate
verification and synthesis into one independent pass. Pin every supported per-call control, currently the model and the
reasoning effort; an unpinned call inherits the caller's session, so the same workflow costs whatever its invoker
happened to be set to. Confirm a cap in a transcript before believing it: the runner drops an option it does not know
without logging anything, so an invented ceiling reads as enforced while the call runs unbounded. Use deterministic code
for collection, filtering, and aggregation when model judgment adds no value.
</routine-workflows>

<feed-each-pass-the-artifact-instead-of-letting-it-rediscover-one>
A pass that must inspect a diff, a tree, or a result set spends nearly all of its wall clock on serial tool round trips,
not on judgment, so the cheapest large win is collecting that artifact once and handing every later pass its path.
Prescribe the single command that writes it and forbid the per-item variant by name, because a model handed a file list
will otherwise inspect one file per turn and turn a two-call workflow into hundreds of round trips. Tool output above
roughly thirty kilobytes is replaced by a short preview and a file path, so write a large artifact to disk and read it
back rather than expecting one command to return it.
</feed-each-pass-the-artifact-instead-of-letting-it-rediscover-one>

<breadth-exception>
Use a larger or dynamic fan-out only when the user explicitly requests the workflow and independent breadth is the
product, such as distinct research sources. Cap the input cardinality, model tier, candidate count, response length,
maximum turns, and total calls. Never put an agent call inside a loop over findings, files, sections, or other
model-produced data.
</breadth-exception>

<enforcement>
Count workflow calls against the same delegation budget as direct subagent spawns. For a mandatory workflow, add a
static repository check that rejects concurrency helpers, per-item call sites, or a call count above its ceiling; do
not add a lifecycle hook when source validation can enforce the invariant without runtime state.
</enforcement>
