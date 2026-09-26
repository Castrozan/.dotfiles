# CI artifact evidence

The tests workflow calls the package-evidence workflow so its completion includes
both traditional tests and independent checks of the complete emitted agent
package. The public production builder supplies the package. These consumer
checks do not regenerate individual assets or modify generator output.

Verdr is pinned to a verified revision in the workflow. The Node scripts use its
schema, runner and native adapters at that boundary; Python checks source bytes,
executable modes and inventory completeness independently of the generator.
Every suite and its expected digest are recorded before execution. Reports retain
the source revision, complete artifact digest, evaluator configuration and native
runtime identity. The archive preserves the complete emitted tree and modes.

Emitted registrations must resolve to the canonical package for all five targets.
Native discovery also compares the complete discovered skill population with the
declared inventory. The startup fixture first proves that its configured server
can write a marker, then requires that discovery leaves the marker absent.

These checks establish CI package preservation, registration origin and measured
native discovery. They do not establish deployment to a user's machine, MCP
invocation, model consumption, hook execution or instruction adherence. Discovery
that is not run must remain explicitly unmeasured in the combined overview.
Claude reload can initialize configured MCP servers; Hermes has no runtime
provisioned in this workflow. Neither limitation is a successful discovery result.

The retained manifest can be consumed by `verdr overview` together with native
JUnit and Cobertura inputs from the same producing run. A failed suite or missing
artifact remains failed or missing evidence. The overall GitHub workflow verdict
is separate from individual test outcomes. Consumers must preserve that distinction
and bind downloaded artifacts to the exact completed run before publishing.
