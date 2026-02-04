---
name: openclaw-doctor
description: Diagnose and fix OpenClaw gateway issues. Use when Telegram bots aren't responding, agents fail to start, or gateway behaves unexpectedly.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

<announcement>
"I'm using the openclaw-doctor skill to diagnose gateway/telegram issues."
</announcement>

<diagnosis_order>
1. Check gateway service status and recent logs
2. Verify telegram providers are starting (look for "[telegram] [name] starting provider")
3. Check for 401 Unauthorized errors (invalid/revoked bot token)
4. Check for stale update-offset files (from recreated bots)
5. Verify config has correct account entries and bindings
6. Test bot token directly with Telegram API
</diagnosis_order>

<config_locations>
Gateway config: ~/.openclaw/openclaw.json
Telegram state: ~/.openclaw/telegram/update-offset-*.json
Bot token file (legacy): ~/.openclaw/telegram-bot-token
Service: systemctl --user status openclaw-gateway
Logs: journalctl --user -u openclaw-gateway
</config_locations>

<telegram_config_structure>
Agents need THREE things to work on Telegram:
1. Agent definition in agents.list (id, model, workspace)
2. Telegram account in channels.telegram.accounts (name, enabled, botToken)
3. Binding connecting agent to telegram account (agentId, match.channel, match.accountId)

Example working config:
```json
"agents": {
  "list": [
    { "id": "robson", "workspace": "/home/user/openclaw/robson" }
  ]
},
"bindings": [
  { "agentId": "robson", "match": { "channel": "telegram", "accountId": "robson" }}
],
"channels": {
  "telegram": {
    "accounts": {
      "robson": {
        "name": "Robson",
        "enabled": true,
        "botToken": "123456789:AAxxxxxxxxxxxxxxxxxxxxxxxxx",
        "dmPolicy": "pairing",
        "groupPolicy": "allowlist",
        "streamMode": "partial"
      }
    }
  }
}
```
</telegram_config_structure>

<common_issues>

## Bot not responding (401 Unauthorized)
Cause: Token was revoked or bot was deleted/recreated in BotFather.
Fix: Get new token from BotFather, update botToken in config, restart gateway.

## Bot recreated with same name
Cause: New bot has different ID, old update-offset file has stale state.
Fix: Delete ~/.openclaw/telegram/update-offset-AGENTNAME.json and restart gateway.

## Missing telegram provider in logs
Cause: Account missing "enabled: true" or no botToken configured.
Fix: Add explicit account entry with enabled: true and botToken.

## Agent bound to wrong bot
Cause: "default" account uses tokenFile, not agent-specific token.
Fix: Create explicit account for each agent with own botToken.

## setMyCommands failed (400: BOT_COMMANDS_TOO_MUCH)
Cause: Too many slash commands registered with Telegram.
Status: Non-critical warning, bot still works.

</common_issues>

<diagnostic_commands>
```bash
# Check gateway status
systemctl --user status openclaw-gateway

# Check which telegram providers started
journalctl --user -u openclaw-gateway --since "5 minutes ago" | grep -E "telegram.*starting"

# Check for errors
journalctl --user -u openclaw-gateway --since "5 minutes ago" | grep -iE "(error|fail|401|403)"

# Test bot token directly
curl -s "https://api.telegram.org/bot<TOKEN>/getMe" | jq .

# Check telegram state files
ls -la ~/.openclaw/telegram/

# Read config accounts
cat ~/.openclaw/openclaw.json | jq '.channels.telegram.accounts'

# Read bindings
cat ~/.openclaw/openclaw.json | jq '.bindings'
```
</diagnostic_commands>

<fix_procedures>

## Add new telegram bot for agent
1. Create bot in BotFather: /newbot
2. Copy the token
3. Edit ~/.openclaw/openclaw.json:
   - Add account entry in channels.telegram.accounts
   - Add binding in bindings array
4. Restart: systemctl --user restart openclaw-gateway
5. Verify: journalctl --user -u openclaw-gateway | grep "starting provider"

## Reset bot after recreation
1. Delete stale offset: rm ~/.openclaw/telegram/update-offset-AGENT.json
2. Update token in config if needed
3. Restart: systemctl --user restart openclaw-gateway

## Update bot token
1. Edit ~/.openclaw/openclaw.json
2. Find channels.telegram.accounts.AGENT.botToken
3. Replace with new token
4. Gateway may hot-reload, or restart manually

</fix_procedures>

<verification>
After any fix:
1. Check logs for "starting provider (@botname)" without errors
2. Test bot token: curl "https://api.telegram.org/bot<TOKEN>/getMe"
3. Send test message to bot
4. Verify message appears in logs
</verification>

<related_files>
Gateway service definition: home-manager module (systemd user service)
Agent workspaces: ~/openclaw/<agent-name>/
Skills deployment: ~/openclaw/<agent-name>/skills/
</related_files>
