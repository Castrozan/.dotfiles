# OPENCLAW_NIX_MODE=1

OpenClaw has a built-in env var that tells the application it's running under a
Nix-managed environment. Detection is strict: `env.OPENCLAW_NIX_MODE === "1"`.

## Where we set it

- **install.nix** — `export OPENCLAW_NIX_MODE=1` in the wrapper script, so
  every `openclaw` CLI invocation (including `doctor`) gets it.
- **gateway-service.nix** — `Environment` in the systemd unit, so the gateway
  daemon process gets it directly.

## What it does

| Area | Behavior |
|---|---|
| Gateway update check | Disabled (no phone-home for version updates) |
| Gateway startup log | Prints `running in Nix mode (config managed externally)` |
| Legacy config migration | Throws hard error instead of silently auto-migrating `openclaw.json` |
| `openclaw gateway install` | Blocked ("service install is disabled") |
| `openclaw gateway uninstall` | Blocked ("service uninstall is disabled") |
| `openclaw node install` | Blocked |
| `openclaw node uninstall` | Blocked |
| Wizard / config-guard | Skips stopping/restarting gateway (lifecycle owned by systemd) |
| `openclaw doctor` | Skips service repair ("skip service updates") |
| Daemon env propagation | `OPENCLAW_NIX_MODE` is in the safe-list forwarded to child processes |
| Plugin SDK | `resolveIsNixMode()` and `isNixMode` exported for plugin authors |
| macOS UI | Read-only Nix mode banner |

## Why it matters

Without this flag, `openclaw doctor` overwrites the Nix-managed systemd unit
with its own version, causing:

- Hardcoded stale `OPENCLAW_BUNDLED_VERSION` env vars
- Uses the install wrapper as `ExecStart` (triggers `npm install` on every
  gateway restart)
- Session path validation errors from mismatched config
