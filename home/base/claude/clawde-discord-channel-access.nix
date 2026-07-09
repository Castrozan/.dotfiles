{
  config,
  lib,
  pkgs,
  ...
}:
let
  discordChannelAccessByAgent = config.clawdeDiscordChannelAccess;
  discordChannelsDirectory = "${config.home.homeDirectory}/.claude/channels/discord";
  mergeAgentAccessScript = ./scripts/merge-discord-agent-access.py;

  mergeAccessCommandFor =
    agentName: agentAccess:
    let
      allowFromArguments = lib.concatMapStringsSep " " (
        userId: "--allow-from-user-id ${lib.escapeShellArg userId}"
      ) agentAccess.allowFrom;
    in
    "$DRY_RUN_CMD ${pkgs.python312}/bin/python3 ${mergeAgentAccessScript}"
    + " --state-directory ${lib.escapeShellArg "${discordChannelsDirectory}/${agentName}"}"
    + " --dm-policy ${lib.escapeShellArg agentAccess.dmPolicy}"
    + lib.optionalString (allowFromArguments != "") " ${allowFromArguments}";
in
{
  options.clawdeDiscordChannelAccess = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options = {
          dmPolicy = lib.mkOption {
            type = lib.types.enum [
              "pairing"
              "allowlist"
              "disabled"
            ];
            default = "allowlist";
            description = "Direct-message gate policy the Discord plugin enforces for this agent.";
          };
          allowFrom = lib.mkOption {
            type = lib.types.listOf lib.types.str;
            default = [ ];
            description = "Discord user IDs allowed to reach this agent by direct message.";
          };
        };
      }
    );
    default = { };
    description = ''
      Declarative Discord plugin DM allowlist per clawde agent, reasserted on
      every rebuild so it never drifts back to the empty default that silently
      drops every inbound message. This owns dmPolicy and allowFrom only; guild
      channel opt-ins (groups) stay with the clawde channel adapter's
      allowedChannelsSecretName merge, and both passes are field-disjoint so
      they compose regardless of activation order. Populate the identifiers from
      private-config so they stay out of the public tree.
    '';
  };

  config = lib.mkIf (discordChannelAccessByAgent != { }) {
    home.activation.deployClawdeDiscordChannelAccess = lib.hm.dag.entryAfter [ "writeBoundary" ] (
      lib.concatStringsSep "\n" (lib.mapAttrsToList mergeAccessCommandFor discordChannelAccessByAgent)
    );
  };
}
