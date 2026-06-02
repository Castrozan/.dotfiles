{ config, lib }:
{
  lucasDiscordUserId = "284143065877184512";
  personalSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/personal";
  jennyHeartbeatPrompt = lib.removeSuffix "\n" (builtins.readFile ./jenny-heartbeat-prompt.md);
  jennyDenyToolPatterns = [
    "mcp__chrome-devtools__*"
    "mcp__browser-use__*"
  ];
}
