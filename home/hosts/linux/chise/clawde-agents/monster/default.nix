{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
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
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
