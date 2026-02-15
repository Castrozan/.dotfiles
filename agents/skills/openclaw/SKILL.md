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
The `openclaw agent` command sends a message to an agent through the gateway and returns the completion. This is the primary way to programmatically interact with agents, test responsiveness, and verify the full pipeline from gateway to model provider and back. Run `openclaw agent --help` for all routing, delivery, session, and thinking options.
</sending_completions_to_agents>

<gateway_and_service_health>
For diagnosis and troubleshooting beyond basic health, use the openclaw-doctor skill instead.
</gateway_and_service_health>

<nix_managed_installation>
OpenClaw is installed and configured through Nix home-manager modules. Search the dotfiles repository for the openclaw home-manager module to find installation, agent config, gateway service, and session patch modules. Each agent must be declared on exactly one machine since Telegram bot tokens support only a single polling instance. Use the dotfiles-expert or nix-expert skills for modifying these modules.
</nix_managed_installation>
