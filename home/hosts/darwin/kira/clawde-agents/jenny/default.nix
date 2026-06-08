{ config, lib, ... }:
let
  personalSkillSetDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets/personal";
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
    personality = builtins.readFile ./personality.md;
  };
}
