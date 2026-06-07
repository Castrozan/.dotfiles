{ lib, hostname, ... }:
{
  clawde.agents.silver = {
    model = "opus";
    permissionMode = "bypassPermissions";
    skillDirectories = [ ];
    personality = import ../clawde/inject-agent-identity.nix {
      inherit lib;
      self = hostname;
      personality = builtins.readFile ./silver-personality.md;
    };
    channel = {
      type = "discord";
      discord.botTokenSecretName = "discord-bot-token-silver";
    };
  };
}
