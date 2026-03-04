# OpenClaw Session Resilience — Diagnosis & Fixes

## Problem Statement

All reliability work so far addresses **gateway process lifecycle** (restarts,
rebuilds, systemd). The actual failure mode is **session-level**: context bloat
causes LLM timeouts with no recovery, leaving agents silently unresponsive.

## Observed Failure (2026-03-04)

Robson went unresponsive. Root cause chain:

1. Session grew to 121k/200k tokens (61% context)
2. Opus request took increasingly long (247–273s per message)
3. Request hit 600s embedded run timeout → `FailoverError: LLM request timed out`
4. Failover tried codex on the **same bloated session** → also timed out (630s)
5. Typing indicator expired at 2m TTL, no error message sent to user
6. Agent went completely silent — message lost, no retry, no notification

Concurrent issues:
- 13 stale-socket health-monitor restarts in 1 hour
- Discord WebSocket dropped (code 1006)
- Slow listener events: 44s, 71s, 247s, 273s, **1250s** (20+ minutes)

## Gap Analysis

### What we built (process-level) ✓
- Restart watcher: resume tasks after gateway restart
- Ensure services after rebuild: survive home-manager reloads
- TimeoutStopSec/KillMode: graceful systemd restart
- Health check timer: detect gateway down
- cacheRetention=long: prompt caching cost savings

### What's missing (session-level) ✗
1. **No context rotation** — sessions grow unbounded until timeout
2. **No timeout recovery** — failed requests are silently dropped
3. **No effective fallback** — failover inherits the same bloated context
4. **No user notification** — agent goes dark with no error message
5. **Stale-socket churn** — 13 restarts/hour suggests systemic issue

## Solutions

### 1. Context Rotation / Session Auto-Reset

**Built-in config exists: `session.reset`**

OpenClaw has a built-in session reset system that can auto-rotate sessions:

```json
{
  "session": {
    "reset": {
      "mode": "daily",
      "atHour": 4,
      "idleMinutes": 120
    }
  }
}
```

- `mode: "daily"` — resets at `atHour` (gateway local time)
- `mode: "idle"` — resets after `idleMinutes` of inactivity
- When both `atHour` and `idleMinutes` are set, whichever expires first triggers reset
- `/new` and `/reset` commands also trigger fresh sessions
- `session.resetByType` and `session.resetByChannel` allow per-type/channel overrides

**Compaction (proactive context shrinking):**

Current config: `compaction.mode: "safeguard"` — this mode has a known bug where it
only triggers AFTER overflow, not before (GitHub #15669). The `"safeguard"` mode also
silently fails on large contexts (~180k tokens), producing "Summary unavailable" instead
of actual summaries (GitHub #7477).

**Proposed but NOT yet available: `autoCompactThreshold`** (GitHub #30411)

Would allow: `compaction.autoCompactThreshold: 0.70` to trigger compaction at 70% of
context window. Currently not implemented in 2026.3.2.

**Context pruning (already configured):**

Current config: `contextPruning.mode: "cache-ttl"`, `ttl: "1h"` — this prunes old tool
results from in-memory context before LLM calls. Key tuning parameters:

- `softTrimRatio: 0.3` — threshold for soft-trim (truncate large tool results)
- `hardClearRatio: 0.5` — threshold for hard-clear (replace tool results with placeholder)
- `keepLastAssistants: 3` — protect final N assistant messages
- `minPrunableToolChars: 50000` — minimum tool result size to consider pruning

**Recommended config changes:**

```
openclaw config set session.reset.mode daily
openclaw config set session.reset.atHour 4
openclaw config set session.reset.idleMinutes 120
openclaw config set agents.defaults.contextTokens 150000
openclaw config set agents.defaults.contextPruning.softTrimRatio 0.3
openclaw config set agents.defaults.contextPruning.hardClearRatio 0.5
```

Setting `contextTokens` to 150000 (instead of 200000 default) provides a 50k buffer
before the model's actual limit, making compaction/pruning trigger earlier.

### 2. LLM Timeout Recovery

**No built-in retry for LLM timeouts.** This is a known gap.

Current behavior: `timeoutSeconds: 600` — if the LLM request exceeds this, it throws
`FailoverError: LLM request timed out`. The failover mechanism then tries the next model
in the fallback list, but on the SAME session context.

OpenClaw's retry policy (docs.openclaw.ai/concepts/retry) only covers channel-level
operations (message send, media upload) — NOT LLM request retries.

The failover cooldown sequence is: 1min -> 5min -> 25min -> 1h (capped). Auth/rate-limit
errors trigger cooldown rotation, but timeout errors are classified differently.

**Workaround: hook-based recovery script**

No config option exists. The workaround is an external hook or cron job that:
1. Monitors for `FailoverError` in logs
2. Runs `openclaw sessions cleanup --enforce` to prune the bloated session
3. Sends a message via `openclaw message send` to notify the user

### 3. Failover with Fresh Session

**No built-in option.** Failover inherits the current session — by design.

From the docs: "Sessions inherit the current context; model fallback does not create
fresh sessions." Profile resets occur only on `/new`, `/reset`, or post-compaction.

**Known issues:**
- Context window not updated when model switches mid-session (GitHub #8240)
- Model failover does not activate on rate limit (GitHub #19249)
- Overloaded error does not trigger model fallback (GitHub #24378)
- Session becomes permanently broken on some tool-call errors (GitHub #25159)

**Workaround:**

The only workaround for context-based failover is to ensure compaction happens BEFORE
the session becomes too large for the fallback model. Since `autoCompactThreshold` is
not yet implemented, the options are:

1. Set `agents.defaults.contextTokens` to a conservative cap (e.g., 150000) — this
   affects the displayed context window but may trigger earlier compaction in `safeguard`
   mode
2. Set `session.reset.idleMinutes` aggressively (e.g., 60) to rotate sessions before
   they bloat
3. Use a cron job to periodically check session token counts and force `/new` when
   threshold is exceeded

### 4. User Notification on Failure

**No built-in config option.** This is a known gap with multiple open GitHub issues.

Relevant issues:
- Agent silent failure: no response sent to user (GitHub #12595, fixed in PR #13746 for
  tool errors specifically)
- Send stop-typing signal when run ends with NO_REPLY (GitHub #8785)
- "Agent failed before reply" errors shown but not always delivered to channel
  (GitHub #19961)

The fix in PR #13746 only addresses tool execution race conditions, not LLM timeout
failures. When the LLM request itself times out, no error message is sent to the user.

**Workaround: hook-based notification**

OpenClaw hooks (`openclaw hooks list`) can listen for events. However:
- `message:sent` hooks don't fire in all paths (GitHub #29203, #29019)
- No `agent:error` or `agent:failed` hook event exists

The practical workaround is an external monitoring script that:
1. Watches `openclaw logs` for timeout/error patterns
2. Sends a message via `openclaw message send --channel telegram --target <user> --message "Agent error: ..."`

### 5. Stale-Socket Restart Frequency

**Partially addressable.** The 13 restarts/hour comes from TWO sources:

**Source A: Our health-check.nix timer (every 2min)**

Our custom health check (`home/modules/openclaw/health-check.nix`) runs every 2 minutes
and restarts the entire gateway if ANY channel account fails its probe. This is
aggressive — a single Discord WebSocket reconnection triggers a full gateway restart.

Fix: increase `openclaw.healthCheck.interval` from `"2min"` to `"5min"` and add
per-channel tolerance before restarting.

**Source B: OpenClaw's internal health-monitor**

The internal health-monitor has known issues:
- Discord provider stuck-restart loop (GitHub #31710, #31760) — health-monitor flags
  Discord as "stuck" every ~5 minutes during normal WebSocket reconnection cycles
- Each restart leaks event listeners, causing duplicate messages
- PR #32920 adds `channelConnectGraceMs` (default 120s) to prevent false positives

**Config key (proposed, may be in 2026.3.2):** `gateway.channelStaleInboundMinutes`
with a default of 15-30 minutes for low-traffic channels.

**Recommended changes:**

1. Increase our health check interval: set `openclaw.healthCheck.interval = "5min"` in
   home-manager config
2. Increase grace period: set `openclaw.healthCheck.gracePeriodSeconds = 180` (from 90)
3. Check if `channelConnectGraceMs` is configurable in 2026.3.2 and set it to 180000

## Implementation Status (2026-03-04)

All actionable items implemented and verified:

### Completed

1. **Session reset config** — `configPatches` in both user configs
   - `session.reset.mode = "daily"`, `atHour = 4`, `idleMinutes = 120`
2. **Context cap + pruning** — `contextTokens = 150000`, `softTrimRatio = 0.3`, `hardClearRatio = 0.5`
3. **Health check tuning** — interval `5min`, grace period `180s` (was 2min/90s)
4. **Timeout recovery service** — `timeout-recovery.nix` + shell scripts
   - Monitors gateway logs for `FailoverError`
   - Auto-runs `openclaw sessions cleanup --enforce` per agent
   - Sends system event notification to user
   - Per-agent cooldown (300s) prevents recovery loops
5. **Config engine fix** — `config-engine.nix` now handles `/` and `"` in jq paths
   - Fixed pre-existing bug where `cacheRetention` patches silently failed
6. **Telegram dmPolicy fix** — default changed from `allowlist` to `pairing`

### Deferred (upstream)

- **autoCompactThreshold** — track GitHub #30411
- **channelConnectGraceMs** — check availability in future releases
- **Agent error hooks** — no `agent:error` event exists yet
