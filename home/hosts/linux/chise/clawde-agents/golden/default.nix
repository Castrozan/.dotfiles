{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
  goldenDenyToolPatterns = [
    "mcp__codex__*"
    "mcp__a2a__*"
    "mcp__claude_ai_Gmail__*"
    "mcp__claude_ai_Google_Calendar__*"
    "mcp__claude_ai_Google_Drive__*"
    "Skill(discord:configure)"
    "Skill(discord:access)"
  ];
in
{
  clawde.agents.golden = {
    channel.type = "discord";
    channel.discord.botTokenSecretName = "discord-bot-token-golden";
    model = "opus";
    skillDirectories = [ shared.personalSkillSetDirectory ];
    permissionMode = "bypassPermissions";
    dailySessionRotation = true;
    heartbeatInterval = "0 8 * * *";
    heartbeatPrompt = builtins.readFile ./morning-briefing-prompt.md;
    denyToolPatterns = goldenDenyToolPatterns;
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
