{
  lib,
  mkEvalCheck,
  helpers,
  self,
}:
let
  cfgWithDiscordChannelAccess = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.claude-code
    {
      clawdeDiscordChannelAccess.test-agent.allowFrom = [ "123456789012345678" ];
    }
  ];
in
{
  clawde-discord-channel-access-dm-policy-defaults-to-allowlist =
    mkEvalCheck "clawde-discord-channel-access-dm-policy-defaults-to-allowlist"
      (cfgWithDiscordChannelAccess.clawdeDiscordChannelAccess.test-agent.dmPolicy == "allowlist")
      "clawdeDiscordChannelAccess.<agent>.dmPolicy must default to allowlist so a bare allowFrom delivers the owner's DMs instead of pair-gating them into an empty inbox";

  clawde-discord-channel-access-emits-merge-activation =
    mkEvalCheck "clawde-discord-channel-access-emits-merge-activation"
      (
        (cfgWithDiscordChannelAccess.home.activation ? deployClawdeDiscordChannelAccess)
        && lib.hasInfix "--dm-policy allowlist" cfgWithDiscordChannelAccess.home.activation.deployClawdeDiscordChannelAccess.data
        && lib.hasInfix "--allow-from-user-id" cfgWithDiscordChannelAccess.home.activation.deployClawdeDiscordChannelAccess.data
      )
      "clawdeDiscordChannelAccess must emit the deployClawdeDiscordChannelAccess activation invoking the merge script with the agent's dm-policy and allow-from arguments; a dropped mkIf guard or broken shell escaping would silently stop reasserting the DM allowlist and let it drift back to empty";
}
