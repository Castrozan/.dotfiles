{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
  monsterDenyToolPatterns = [
    "mcp__codex__*"
    "mcp__a2a__*"
    "mcp__chrome-devtools__*"
    "mcp__browser-use__*"
    "mcp__claude_ai_Gmail__*"
    "mcp__claude_ai_Google_Calendar__*"
    "mcp__claude_ai_Google_Drive__*"
    "Bash(sudo:*)"
    "Bash(rm:*)"
    "Bash(dd:*)"
    "Bash(mkfs:*)"
    "Bash(shutdown:*)"
    "Bash(reboot:*)"
    "Bash(curl:*)"
    "Bash(wget:*)"
    "Edit"
    "Write"
    "NotebookEdit"
    "Skill(discord:configure)"
    "Skill(discord:access)"
  ];
in
{
  clawde.agents.monster = {
    channel.type = "discord";
    channel.discord.botTokenSecretName = "discord-bot-token-monster";
    model = "opus";
    skillDirectories = [ ];
    permissionMode = "bypassPermissions";
    dailySessionRotation = true;
    heartbeatInterval = "*/30 * * * *";
    heartbeatPrompt = shared.agentHeartbeatPrompt;
    denyToolPatterns = monsterDenyToolPatterns;
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
