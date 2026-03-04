# OpenClaw Gateway Restart Behavior

## SIGUSR1 is a full process restart, not a hot reload

When the gateway receives SIGUSR1 (from an agent calling the gateway tool, or `systemctl --user kill -s USR1 openclaw-gateway`), the internal handler always performs a full process restart via supervisor exit. There is no config to change this — it is hardwired in `gateway-cli-CuFEx2ht.js` inside `restartGatewayProcessWithFreshPid()`.

The `gateway.reload.mode` config (`hybrid`, `hot`, `restart`, `off`) controls only what happens when the config *file* changes on disk. It has no effect on SIGUSR1 behavior.

Active sessions and WebSocket connections are destroyed on SIGUSR1. Sessions persist to disk and can be resumed, but in-flight tool calls and streaming responses are lost.

## Drain mechanism

Before exiting, the gateway drains pending work (queue items, pending replies, active embedded runs). The drain timeout is hardcoded at 30 seconds (`DEFAULT_DEFERRAL_MAX_WAIT_MS = 3e4`) with 500ms poll interval. If tasks don't complete within 30s, the gateway exits anyway.

Multiple SIGUSR1 signals within 30 seconds are coalesced into a single restart, with a 30-second cooldown between restarts.

## Browser tool orphan processes

Agents using the browser tool spawn chromium child processes (plus `chrome_crashpad` handlers). These processes become orphans when the gateway exits — they don't respond to SIGTERM because they lost their parent process.

The systemd service uses `KillMode = "control-group"` so that on stop, SIGTERM is sent to all processes in the cgroup (including chromium orphans), not just the main process. `TimeoutStopSec = "10s"` limits the wait before SIGKILL, since the gateway already handles its own 30s internal drain before exiting — systemd's job is just cleanup.

Previously `KillMode = "mixed"` + `TimeoutStopSec = "45s"` caused the service to sit in `deactivating (stop-sigterm)` for 30-45 seconds while waiting for chromium orphans that never received SIGTERM.

## Authorization

SIGUSR1 restart requires authorization via either the gateway tool (internal) or `commands.restart = true` in config. Unauthorized SIGUSR1 signals are logged and ignored.
