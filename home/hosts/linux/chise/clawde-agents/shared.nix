{ config, lib }:
{
  lucasDiscordUserId = "284143065877184512";
  personalSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/personal";
  agentHeartbeatPrompt = lib.removeSuffix "\n" (builtins.readFile ./agent-heartbeat-prompt.md);
}
