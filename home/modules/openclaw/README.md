<!-- Changes to this file MUST use the /docs skill. -->

# OpenClaw

This instance runs 4 agents (robson, jenny, monster, silver) across Telegram and Discord channels, managed declaratively through Nix at `home/modules/openclaw/`. The gateway runs as a systemd user service.

## Gateway Restart

SIGUSR1 always triggers a full process restart via supervisor exit — there is no config knob to make it hot-reload. The `gateway.reload.mode` setting (`hybrid`, `hot`, `restart`, `off`) controls only config file change detection, not SIGUSR1 behavior. Active sessions and WebSocket connections are destroyed; sessions persist to disk but in-flight tool calls and streaming responses are lost.

The gateway drains pending work before exiting: queue items, pending replies, and active embedded runs. The drain timeout is hardcoded at 30 seconds with 500ms poll interval and a 30-second cooldown between restarts. Multiple SIGUSR1 signals coalesce into one restart.

Agents using the browser tool spawn chromium child processes that become orphans on gateway exit. The systemd service uses `KillMode = "control-group"` so SIGTERM reaches all cgroup processes (not just main), and `TimeoutStopSec = "10s"` since the gateway already handles its own 30s drain internally. Previously `KillMode = "mixed"` + `TimeoutStopSec = "45s"` caused 30-45 second stuck `deactivating` states waiting for chromium orphans that never received SIGTERM.

SIGUSR1 restart requires authorization via the gateway tool or `commands.restart = true`. Unauthorized signals are ignored.

## Discord

OpenClaw always requests `GatewayIntents.MessageContent`. If not enabled in Discord Developer Portal under Bot > Privileged Gateway Intents, the gateway crashes with fatal error 4014 and crash-loops. This must be enabled per bot application — no config-side workaround exists.

Voice connections require the `@snazzah/davey` npm package. Without it, joining a voice channel crashes the entire gateway. The `voice.enable = true` config is dangerous until this dependency is installed.

`dmPolicy: "pairing"` means bots silently ignore DMs from unpaired users — they appear online but don't respond. Users must send `/pair` first. The `allowFrom` list in the Nix module persists paired user IDs across rebuilds (without it, the jq patch engine's full-object replacement wipes locally-added pairings).

## Model Providers

NVIDIA NIM free tier models are not viable as agent primaries. DeepSeek V3.2 outputs raw JSON content blocks instead of plain text. Llama 3.3 70B rejects parallel tool calls. Kimi K2.5 intermittently hangs. Keep NVIDIA models only in the fallback chain, never as primary.

The fallback chain must cross providers — having the same provider as both primary and first fallback is useless during rate limits (e.g., Anthropic primary with Anthropic fallback both fail together).

Provider config requires `baseUrl` (string) and `models` (array of `{id, name}`). Non-built-in providers need `api: "openai-completions"`. `models.mode = "merge"` overlays on the built-in models.json. `memorySearch` has its own separate apiKey/provider/model config.

## Nix Config Architecture

`config-declarations.nix` declares all patches as jq-path to value pairs. `config-engine.nix` applies them via jq on every rebuild, writing atomically. The app can freely modify `openclaw.json` between rebuilds; next rebuild re-pins declared fields. Secret patches use home-manager agenix paths at `~/.secrets/`.

The patch engine uses jq `=` assignment (full object replacement), not merge. Any field not declared in the Nix module gets wiped on rebuild if it's nested under a declared parent object. This is why `allowFrom` for Discord needed its own module option rather than relying on local config edits.
