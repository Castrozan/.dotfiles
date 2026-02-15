---
name: openclaw
description: OpenClaw multi-agent platform. Use when working with agents, gateway, channels, config, or any openclaw CLI operation.
---

<announcement>
"I'm using the openclaw skill."
</announcement>

<discovering_openclaw_capabilities>
OpenClaw is a self-documenting CLI. Every command and subcommand supports `--help` with usage, flags, and examples. Always run `openclaw --help` to discover top-level commands, and `openclaw <command> --help` for specifics. The CLI output is the source of truth for syntax and available options — never guess flags or endpoints. Official documentation lives at the URL printed in each help output under `Docs:`.
</discovering_openclaw_capabilities>

<sending_completions_to_agents>
The `openclaw agent` command sends a message to an agent through the gateway and returns the completion. This is the primary way to programmatically interact with agents, test responsiveness, and verify the full pipeline from gateway to model provider and back. Run `openclaw agent --help` for all routing, delivery, session, and thinking options. The `--json` flag returns structured output including the reply text, model used, token usage, and duration — use this for programmatic verification. To verify all agents are healthy, iterate over the agent list and send a trivial message to each, checking that every response contains a valid reply.
</sending_completions_to_agents>

<gateway_and_service_health>
The gateway runs as a systemd user service. Use `openclaw status` for a dashboard view of gateway reachability, channel state, agent count, and session summary. The `--deep` flag probes each connected channel. The `openclaw health` command returns a quick programmatic health check. Gateway logs are available through journalctl for the `openclaw-gateway` user unit — filter by recency and error patterns when diagnosing issues. For diagnosis and troubleshooting beyond basic health, use the openclaw-doctor skill instead.
</gateway_and_service_health>

<nix_managed_installation>
OpenClaw is installed and configured through Nix home-manager modules in the dotfiles repository. Look for the openclaw home module directory — it contains separate modules for install, config, gateway service, memory sync, and session patches, each following single responsibility. The install module manages the npm package version and applies runtime patches. The config module declares agents, and each agent must be declared on exactly one machine since Telegram bot tokens support only a single polling instance. Use the dotfiles-expert or nix-expert skills for modifying these modules.
</nix_managed_installation>
