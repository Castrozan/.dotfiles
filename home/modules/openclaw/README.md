<!-- Changes to this file MUST use the /docs skill. -->

# OpenClaw

Multi-agent platform running across Telegram and Discord, managed declaratively through Nix. The gateway runs as a systemd user service. Agent declarations, channel bindings, model config, and secrets are all Nix-managed — the app can modify `openclaw.json` between rebuilds but next rebuild re-pins declared fields.

## Nix Mode

`OPENCLAW_NIX_MODE=1` tells OpenClaw it runs under external config management. Set in `install.nix` (wrapper script) for CLI and in `systemd-service.nix` (Environment) for the daemon. It disables update checks, blocks service install/uninstall commands, skips wizard lifecycle management, and prevents `openclaw doctor` from overwriting the Nix-managed systemd unit. Without this flag, doctor replaces the unit with a stale hardcoded version that triggers `npm install` on every gateway restart.

## Patch Engine

`config-declarations.nix` declares patches as jq-path to value pairs. `config-engine.nix` applies them via jq on every rebuild, writing atomically. The engine uses jq `=` assignment (full object replacement), not merge — any field not declared in the Nix module gets wiped on rebuild if nested under a declared parent object. This is why per-agent options like `allowFrom` need their own Nix module option rather than relying on local config edits surviving rebuilds. Secret patches inject agenix-decrypted files at `~/.secrets/`.

## Gateway Restart

SIGUSR1 always triggers a full process restart via supervisor exit — no config knob exists for hot-reload. The `gateway.reload.mode` setting controls only config file change detection, not SIGUSR1 behavior. Active sessions are destroyed; they persist to disk but in-flight tool calls and streaming responses are lost.

The gateway drains pending work before exiting (queue items, pending replies, active embedded runs). The drain timeout is hardcoded at 30 seconds with a 30-second cooldown between restarts. Multiple SIGUSR1 signals coalesce.

Agents using the browser tool spawn chromium child processes that become orphans on gateway exit. The systemd service uses `KillMode = "control-group"` so SIGTERM reaches all cgroup processes and `TimeoutStopSec = "10s"` since the gateway handles its own drain internally. Without this, chromium orphans cause 30-45 second stuck `deactivating` states.

## Model Failover

No per-LLM-request timeout exists. The only timeout is `agents.defaults.timeoutSeconds` which covers the entire agent turn. When the primary provider hangs silently (no fast 429), the request consumes the full turn budget and the fallback chain never executes. The fallback only activates on the next message after the provider enters cooldown. The missing upstream config is `agents.defaults.model.timeoutSeconds` — a per-request deadline independent of the turn timeout.

The fallback chain must cross providers. Same provider as both primary and first fallback is useless during rate limits — both fail together. NVIDIA NIM free tier models are not viable as primaries: DeepSeek V3.2 outputs raw JSON content blocks, Llama 3.3 70B rejects parallel tool calls, Kimi K2.5 intermittently hangs. Keep NVIDIA models only in the fallback chain.

Provider config requires `baseUrl` (string) and `models` (array of `{id, name}`). Non-built-in providers need `api: "openai-completions"`. `models.mode = "merge"` overlays on built-in models.json. `memorySearch` has its own separate apiKey/provider/model config.

## Discord

OpenClaw always requests `GatewayIntents.MessageContent`. If not enabled in Discord Developer Portal under Bot > Privileged Gateway Intents, the gateway crashes with fatal error 4014 and crash-loops. Must be enabled per bot application — no config-side workaround.

Voice connections require the `@snazzah/davey` npm package. Without it, joining a voice channel crashes the entire gateway.

`dmPolicy: "pairing"` means bots silently ignore DMs from unpaired users — they appear online but don't respond. Users must send `/pair` first.
