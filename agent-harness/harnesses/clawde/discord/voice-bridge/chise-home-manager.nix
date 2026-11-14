{ config, lib, ... }:
let
  bridge = config.clawdeDiscordVoiceBridge;
  authorizedAgents = lib.filterAttrs (
    name: agent:
    agent.channel.type == "discord"
    && lib.elem bridge.listenerDiscordUserId (
      lib.attrByPath [ name "allowFrom" ] [ ] config.clawdeDiscordChannelAccess
    )
  ) config.clawde.agents;
in
{
  config = lib.mkIf (bridge != null) {
    clawdeDiscordVoiceIdentities = lib.mapAttrs (name: agent: {
      botTokenSecretName = agent.channel.discord.botTokenSecretName;
      ownerHost = "chise";
      listenerUserId = bridge.listenerDiscordUserId;
      guildId = bridge.answeredGuildId;
      preferredAgent = name;
    }) authorizedAgents;
  };
}
