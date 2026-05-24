_: {
  clawde.agents.silver = {
    model = "opus";
    permissionMode = "bypassPermissions";
    skillDirectories = [ ];
    personality = builtins.readFile ./silver-personality.md;
    channel = {
      type = "discord";
      discord.botTokenSecretName = "discord-bot-token-silver";
    };
  };
}
