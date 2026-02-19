---
name: openclaw
description: OpenClaw multi-agent platform. Use when working with agents, gateway, channels, config, CLI operations, or diagnosing gateway issues. Also use when Telegram bots aren't responding, agents fail to start, or gateway behaves unexpectedly.
---

<announcement>
"I'm using the openclaw skill."
</announcement>

<discovering_capabilities>
OpenClaw is a self-documenting CLI. Every command and subcommand supports --help with usage, flags, and examples. Always run openclaw --help to discover top-level commands, and openclaw subcommand --help for specifics. The CLI output is the source of truth for syntax and available options. Never guess flags or endpoints.
</discovering_capabilities>

<sending_completions>
The openclaw agent command sends a message to an agent through the gateway and returns the completion. This is the primary way to programmatically interact with agents, test responsiveness, and verify the full pipeline. Run openclaw agent --help for all routing, delivery, session, and thinking options.
</sending_completions>

<reading_chat_history>
Use the script at agents/skills/openclaw/scripts/read-agent-chat.sh to read an agent's chat history from session JSONL files. Run with --help for all options: agent name, --list sessions, --limit N, --session UUID, --tools to include tool calls.
</reading_chat_history>

<nix_managed_installation>
OpenClaw is installed and configured through Nix home-manager modules. Search the dotfiles repository for the openclaw home-manager module to find installation, agent config, gateway service, and session patch modules. Each agent must be declared on exactly one machine since Telegram bot tokens support only a single polling instance.
</nix_managed_installation>

<gateway_diagnosis>
For gateway issues, use openclaw status for a dashboard view. The --deep flag probes each connected channel. openclaw health returns a quick programmatic health check. Gateway logs: journalctl --user -u openclaw-gateway.

NEVER run openclaw doctor --non-interactive — it overwrites config and breaks things.
</gateway_diagnosis>

<diagnosis_order>
1. Gateway status: openclaw status or systemctl --user status openclaw-gateway
2. Config valid: check ~/.openclaw/openclaw.json then gateway config.get
3. Logs: journalctl --user -u openclaw-gateway -n 30 --no-pager
4. Look for: [telegram] startup, No API key found, Config invalid, ECONNREFUSED, 401 Unauthorized
5. Auth profile: check auth-profiles.json in the agent workspace
6. Test bot token: curl the Telegram getMe endpoint
7. Telegram state files in ~/.openclaw/telegram/
</diagnosis_order>

<config_architecture>
Single JSON file at ~/.openclaw/openclaw.json is the source of truth. Do not manage via Nix activation scripts or merge strategies. Let openclaw manage its own config locally. Nix manages: workspace symlinks and package installation only. Watch for port mismatch between gateway.port in config and systemd service env.
</config_architecture>

<telegram_setup>
Agents need three things for Telegram: agent definition in agents.list (id, model, workspace), Telegram account in channels.telegram.accounts (name, enabled, botToken), and binding connecting agent to telegram account (agentId, match.channel, match.accountId). Never put tokens inline — use tokenFile pointing to a chmod 600 file.
</telegram_setup>

<common_issues>
Bot not responding (401): Token revoked or bot recreated. Get new token from BotFather, update config, restart.
Bot recreated with same name: New bot has different ID. Remove update-offset file at ~/.openclaw/telegram/update-offset-AGENT.json, restart gateway.
Missing telegram provider: Account needs enabled: true and botToken configured.
Agent bound to wrong bot: "default" account uses tokenFile, not agent-specific token. Create explicit account per agent with own botToken.
Channels not starting: Check plugins.entries.telegram.enabled and channels.telegram.enabled are both true. Delete stale offset files if switching bots.
setMyCommands failed (400): Non-critical warning, bot still works.
Missing auth profile: Auth-profiles.json in the agent workspace must exist with valid provider token.
No config file: Write fresh openclaw.json with channels, gateway (port, auth), agents, plugins. Use gateway config.patch locally or write directly via SSH for remote.
</common_issues>

<multi_bot_setup>
When multiple bots share Telegram groups: each bot's groupAllowFrom must include the other bot's ID. Shared group entries need both IDs in allowFrom. Set requireMention: false for bot-to-bot chat. Bot IDs come from agenix secrets substituted at activation time.
</multi_bot_setup>

<remote_management>
Manage remote instances via SSH. Prefix openclaw commands with the correct PATH export: ssh user@host "export PATH=\$HOME/.npm-global/bin:\$PATH; openclaw status". Same pattern for logs (journalctl --user -u openclaw-gateway) and restarts (systemctl --user restart openclaw-gateway). After remote restart, verify channels start by checking logs for "[telegram] starting provider".
</remote_management>

<fix_procedures>
Add new telegram bot: Create bot in BotFather /newbot, store token in chmod 600 file, edit config to add account + binding, restart gateway, verify logs show "starting provider (@botname)".

Reset bot after recreation: Remove update-offset file for the agent from ~/.openclaw/telegram/, update token if needed, restart gateway.

Retrieve lost bot token: BotFather → /mybots → select bot → "API Token". Token format: bot-id:alphanumeric-string.
</fix_procedures>

<verification>
After any fix: logs show "starting provider (@botname)" without errors, token test via Telegram getMe succeeds, send test message to bot, message appears in logs.
</verification>
