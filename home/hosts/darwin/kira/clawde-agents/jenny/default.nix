{ config, lib, ... }:
let
  personalSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/personal";
  jennyDenyToolPatterns = [
    "mcp__chrome-devtools__*"
    "mcp__browser-use__*"
  ];
in
{
  clawde.agents.jenny = {
    channel.type = "discord";
    channel.discord.botTokenSecretName = "discord-bot-token-jenny";
    model = "claude-opus-4-8";
    skillDirectories = [ personalSkillSetDirectory ];
    permissionMode = "bypassPermissions";
    activeHoursStart = 8;
    activeHoursEnd = 20;
    dailySessionRotation = true;
    heartbeatInterval = "*/30 * * * *";
    heartbeatPrompt = lib.removeSuffix "\n" (builtins.readFile ./heartbeat-prompt.md);
    denyToolPatterns = jennyDenyToolPatterns;
    personality = builtins.readFile ./personality.md;
  };
}
