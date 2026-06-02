{ config, lib, ... }:
let
  shared = import ../shared.nix { inherit config lib; };
in
{
  clawde.agents.claude = {
    channel.type = "discord";
    channel.discord.botTokenSecretName = "discord-bot-token-claude";
    model = "opus";
    skillDirectories = [ shared.personalSkillSetDirectory ];
    permissionMode = "bypassPermissions";
    personality = builtins.replaceStrings [ "@lucasDiscordUserId@" ] [ shared.lucasDiscordUserId ] (
      builtins.readFile ./personality.md
    );
  };
}
