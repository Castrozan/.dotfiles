{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
in
{
  clawde.agents.clever = {
    channel.type = "discord";
    channel.discord.botTokenSecretName = "discord-bot-token-clever";
    model = "opus";
    skillDirectories = [ shared.personalSkillSetDirectory ];
    permissionMode = "bypassPermissions";
    activeHoursStart = 8;
    activeHoursEnd = 20;
    dailySessionRotation = true;
    heartbeatInterval = "*/30 * * * *";
    heartbeatPrompt = shared.agentHeartbeatPrompt;
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
