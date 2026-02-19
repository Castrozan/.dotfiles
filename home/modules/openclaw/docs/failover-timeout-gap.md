# Model failover timeout gap (v2026.2.15)

OpenClaw has no per-LLM-request timeout. The only timeout is `agents.defaults.timeoutSeconds` (default 600s), which controls the entire agent turn — LLM inference, tool calls, everything. When the primary provider hangs (no fast 429, just silence), the request consumes the full turn budget. The failover chain (`agents.defaults.model.fallbacks`) never executes because the turn is already dead by the time the timeout fires.

The missing config key is `agents.defaults.model.timeoutSeconds`: a deadline for a single LLM request, independent of the turn timeout. With it set to e.g. 60s and the turn timeout at 300s, the primary would fail fast and hand off to the first fallback with 240s remaining.

## Workaround

We set `agents.defaults.timeoutSeconds` to 300 in `config-declarations.nix`. This halves the worst-case hang (from 10 min to 5 min) but still wastes the entire turn when the primary hangs. The fallback only activates on the _next_ message, after the provider enters cooldown.

## Upstream references

- openclaw/openclaw#9743 — single timeout triggers extended cooldown, blocks fallbacks
- openclaw/openclaw#17613 — embedded agent hangs full timeoutSeconds before FailoverError
- openclaw/openclaw#9300 — requests hanging 12-23 minutes without appropriate timeout
