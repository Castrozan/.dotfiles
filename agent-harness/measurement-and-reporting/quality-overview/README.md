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

## Published overview

The existing reports deployment workflow also listens for completed `tests` runs
from pushes to this repository's `main` branch. Its overview job selects artifacts
by producing run, revision, job and successful upload interval, including failed
runs. Partial retries retain evidence from jobs GitHub did not rerun, with their
original attempt and timestamps verified against run history. A rerun job cannot
fall back to its earlier output. Expired, ambiguous or missing artifacts remain
explicit gaps. Exact artifact IDs are downloaded through the GitHub archive API
and their SHA-256 digests are checked before bounded extraction. It imports four native JUnit tiers and
Python Cobertura coverage beside the frozen package evidence. Swift, QML and Lua
testcase import, Swift coverage import and mutation testing retain their
specific unmeasured status.

The Python collector owns GitHub metadata and artifact selection. The JavaScript
adapter calls the pinned portable Verdr schemas and report builder. The existing
snapshot publisher owns authenticated ingestion. Neither report assembly nor
publication runs a model, production MCP server or browser.

Reports and unchanged raw inputs are stored under `reports/overview/RUN/ATTEMPT/`
in the existing snapshots bucket. `snapshot.json` is written after the report and
details are available. A retry reuses that completed receipt rather than replacing
it. The job promotes an ingestion snapshot only while its source revision is the
current `main` and its attempt is still current. Older reports remain attributable
to their producing execution and do not overwrite the current snapshot.

The `dotfiles-quality-overview` ingestion payload keeps the producing workflow's
conclusion separate from the portable overview. Its source identifies the test
run, not the later publisher run. Hosted viewers must recompute each measurement's
freshness and retain its exact scope, validity, outcome and source links.

After retaining and publishing the diagnostic report, the publisher requires all
11 mandatory evidence items to be usable. Missing or malformed evidence makes the
publication workflow fail. A valid report of failed tests remains usable evidence;
the test workflow owns its execution verdict. Deliberately unmeasured capabilities
and unsupported report formats keep their declared status.
