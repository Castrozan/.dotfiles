{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
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
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
