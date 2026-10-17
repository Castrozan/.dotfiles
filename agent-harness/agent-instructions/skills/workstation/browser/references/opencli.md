# OpenCLI browser jobs

## Scope

Chrome DevTools remains the primary interactive browser. OpenCLI supplies reusable site commands and the isolated
fallback permitted by `SKILL.md`. Its profiles carry their own logins; never assume access to Chrome Global accounts.

## Workflow ownership

Use `opencli` for site adapters and capability discovery. Public adapters run without a browser; browser-backed adapters
automatically acquire a complete job. Put all commands of a multi-step browser workflow inside one `opencli-run`
invocation, otherwise each invocation starts a new browser and loses its live page state. Read both commands' `--help`
for syntax. The runner owns startup, exclusive access, bounded execution and cleanup after success or failure.

Choose a named profile when a task needs persistent authentication. Use a headed job for the initial human login; the
profile persists after its processes exit. Concurrent jobs fail without interrupting the current owner. Retry after the
owner finishes; never kill another job or substitute the user's shared browser.

## Reusable site work

Inspect `opencli list` before reimplementing a supported site's extraction. Use the site's read commands when their
output matches the task, and validate completeness against the requested scope. A successful exit does not establish
that a virtualized thread or paginated collection was read completely.

When repeated work needs a new command, use `opencli adapter init`, `adapter check` and `adapter test`. Keep durable
adapters in the repository that owns their workflow. Network capture and static endpoint discovery provide evidence
for building adapters; an endpoint found in a script is a candidate until an actual request verifies its behavior.
