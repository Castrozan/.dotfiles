---
name: openclaw-doctor
description: Diagnose and fix OpenClaw gateway issues. Use when Telegram bots aren't responding, agents fail to start, or gateway behaves unexpectedly.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the openclaw-doctor skill to diagnose gateway/telegram issues."
</announcement>

<diagnosis_order>
1. Gateway status: `openclaw status` or `systemctl --user status openclaw-gateway`
2. Config exists and valid: `cat ~/.openclaw/openclaw.json` then `gateway(action=config.get)`
3. Logs: `journalctl --user -u openclaw-gateway -n 30 --no-pager`
4. Check for: `[telegram]` startup, `No API key found`, `Config invalid`, `ECONNREFUSED`, `401 Unauthorized`
5. Auth profile: `cat ~/.openclaw/agents/main/agent/auth-profiles.json`
6. Test bot token: `curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | jq .`
7. Telegram state files: `ls -la ~/.openclaw/telegram/`
</diagnosis_order>

<config_architecture>
OpenClaw config is a single JSON file at `~/.openclaw/openclaw.json` — the source of truth.

**Do not** manage it via Nix activation scripts or merge strategies — this causes override bugs. Let openclaw manage its own config locally. Nix should only manage: workspace symlinks (identity/rules/skills) and package installation.

**Port mismatch**: gateway port in config (`gateway.port`) vs systemd service env (`OPENCLAW_GATEWAY_PORT`) can diverge — these must match.
</config_architecture>

<telegram_config_structure>
Agents need THREE things for Telegram:
1. Agent definition in `agents.list` (id, model, workspace)
2. Telegram account in `channels.telegram.accounts` (name, enabled, botToken)
3. Binding connecting agent to telegram account (agentId, match.channel, match.accountId)

Token storage: Never put inline in config. Use `tokenFile` pointing to a file (`chmod 600`).
</telegram_config_structure>

<common_issues>

## Bot not responding (401 Unauthorized)
Token revoked or bot deleted/recreated in BotFather.
Fix: Get new token from BotFather, update botToken in config, restart gateway.

## Bot recreated with same name
New bot has different ID, old update-offset file has stale state.
Fix: `rm ~/.openclaw/telegram/update-offset-AGENT.json` and restart gateway.

## Missing telegram provider in logs
Account missing `enabled: true` or no botToken configured.
Fix: Add explicit account entry with enabled: true and botToken.

## Agent bound to wrong bot
"default" account uses tokenFile, not agent-specific token.
Fix: Create explicit account for each agent with own botToken.

## Channels not starting after restart
Check `plugins.entries.telegram.enabled` and `channels.telegram.enabled` are both `true`.
After config changes: SIGUSR1 or service restart. Delete stale offset files if switching bots.

## setMyCommands failed (400: BOT_COMMANDS_TOO_MUCH)
Non-critical warning, bot still works.

## Missing auth profile
`~/.openclaw/agents/main/agent/auth-profiles.json` must exist with valid provider token.

## No config file
Write fresh `openclaw.json` with: `channels`, `gateway` (port, auth), `agents`, `plugins`.
Use `gateway(action=config.patch)` for local, or write directly via SSH for remote.

</common_issues>

<multi_bot_setup>
## Multi-Bot Setup (shared groups)

When multiple bots share Telegram groups:
- Each bot's `groupAllowFrom` must include the other bot's ID
- `groups.*` entries need both IDs in `allowFrom`
- Shared group: `requireMention: false` for bot-to-bot chat
- Bot IDs come from agenix secrets (substituted at activation time)
</multi_bot_setup>

<remote_management>
## Remote Instance Management (via SSH)

```bash
ssh user@host "export PATH=\$HOME/.npm-global/bin:\$PATH; openclaw status"
ssh user@host "journalctl --user -u openclaw-gateway -n 30 --no-pager"
ssh user@host "systemctl --user restart openclaw-gateway"
```

Verify channels start after restart by checking logs for `[telegram] starting provider`.
</remote_management>

<fix_procedures>

## Add new telegram bot
1. Create bot in BotFather: /newbot
2. Copy token, store in file (chmod 600)
3. Edit config: add account + binding
4. Restart: `systemctl --user restart openclaw-gateway`
5. Verify: logs show "starting provider (@botname)"

## Reset bot after recreation
1. `rm ~/.openclaw/telegram/update-offset-AGENT.json`
2. Update token if needed
3. Restart gateway

## Retrieve lost bot token
1. BotFather → `/mybots` → select bot → "API Token"
2. Or search BotFather history for "Use this token to access the HTTP API"
3. Token format: `<bot-id>:<alphanumeric-string>`

</fix_procedures>

<verification>
After any fix:
1. Logs show "starting provider (@botname)" without errors
2. Token test: `curl "https://api.telegram.org/bot<TOKEN>/getMe"`
3. Send test message to bot
4. Message appears in logs
</verification>
