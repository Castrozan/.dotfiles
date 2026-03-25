---
name: openclaw
description: OpenClaw multi-agent platform — agents, gateway, grid coordination, A2A protocol, cron jobs, Telegram bots, recurring tasks, inter-agent communication, and external agent protocols.
---

<announcement>
"I'm using the openclaw skill."
</announcement>

<subskills>
For grid coordination and inter-agent communication, read `grid.md`. For A2A protocol with external agents, read `a2a.md`. For cron jobs and recurring assistant tasks, read `assistant-cron.md`.
</subskills>

<cli>
OpenClaw is a self-documenting CLI — every command supports --help. Use it as the source of truth for syntax and available options. The read-agent-chat.sh script in this skill's scripts directory reads chat history from session JSONL files.
</cli>

<nix_managed_installation>
OpenClaw is installed and configured through Nix home-manager modules. Each agent must be declared on exactly one machine since Telegram bot tokens support only a single polling instance.
</nix_managed_installation>

<gateway_diagnosis>
Use openclaw status (--deep for channel probes) or openclaw health for quick checks. Logs: journalctl --user -u openclaw-gateway. NEVER run openclaw doctor --non-interactive — it overwrites config and breaks things.

Diagnosis order: gateway status → config validity (~/.openclaw/openclaw.json) → logs → look for [telegram] startup errors, auth failures, ECONNREFUSED → test bot tokens via Telegram getMe.
</gateway_diagnosis>

<config_architecture>
Single JSON file at ~/.openclaw/openclaw.json is the source of truth. Do not manage via Nix activation scripts or merge strategies — let openclaw manage its own config locally. Nix manages workspace symlinks and package installation only. Watch for port mismatch between gateway.port in config and systemd service env.
</config_architecture>

<telegram_setup>
Agents need three things for Telegram: agent definition in agents.list, Telegram account in channels.telegram.accounts (with botToken via tokenFile, never inline), and binding connecting agent to account. Never put tokens inline — use tokenFile pointing to a chmod 600 file.
</telegram_setup>

<common_issues>
Bot not responding (401): token revoked or bot recreated — get new token, update config, restart. Bot recreated with same name: new bot has different ID — remove update-offset file, restart. Missing telegram provider: account needs enabled: true and botToken. Agent bound to wrong bot: "default" account uses tokenFile, create explicit account per agent. Channels not starting: check both plugins.entries.telegram.enabled and channels.telegram.enabled. Missing auth profile: auth-profiles.json must exist in agent workspace.
</common_issues>

<multi_bot_setup>
When multiple bots share Telegram groups: each bot's groupAllowFrom must include the other bot's ID. Set requireMention: false for bot-to-bot chat. Bot IDs come from agenix secrets substituted at activation time.
</multi_bot_setup>

<remote_management>
Manage remote instances via SSH with PATH export for npm-global/bin. Same pattern for logs and restarts. After restart, verify channels start by checking logs for "[telegram] starting provider".
</remote_management>

<fix_procedures>
Add new bot: BotFather /newbot → store token in chmod 600 file → edit config → restart → verify logs. Reset after recreation: remove update-offset file → update token → restart. Retrieve lost token: BotFather → /mybots → select → "API Token".
</fix_procedures>
