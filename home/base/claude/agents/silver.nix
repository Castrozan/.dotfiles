{ hostname, ... }:
let
  personalityWithHostIdentity = builtins.replaceStrings [ "@silverSelf@" ] [ hostname ] (
    builtins.readFile ./silver-personality.md
  );
in
{
  clawde.agents.silver = {
    model = "opus";
    permissionMode = "bypassPermissions";
    skillDirectories = [ ];
    personality = personalityWithHostIdentity;
    channel = {
      type = "discord";
      discord.botTokenSecretName = "discord-bot-token-silver";
    };
  };
}
