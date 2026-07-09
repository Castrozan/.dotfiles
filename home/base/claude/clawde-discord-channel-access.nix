{
  config,
  lib,
  pkgs,
  ...
}:
let
  discordChannelAccessByAgent = config.clawdeDiscordChannelAccess;
  discordChannelsDirectory = "${config.home.homeDirectory}/.claude/channels/discord";

  renderedAccessFileFor =
    agentName: agentAccess:
    pkgs.writeText "discord-channel-access-${agentName}.json" (
      builtins.toJSON {
        inherit (agentAccess) dmPolicy allowFrom groups;
        pending = { };
      }
    );

  deployAccessFileCommandFor =
    agentName: agentAccess:
    "$DRY_RUN_CMD ${pkgs.coreutils}/bin/install -Dm600 ${renderedAccessFileFor agentName agentAccess} "
    + lib.escapeShellArg "${discordChannelsDirectory}/${agentName}/access.json";
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
          groups = lib.mkOption {
            type = lib.types.attrsOf (
              lib.types.submodule {
                options = {
                  requireMention = lib.mkOption {
                    type = lib.types.bool;
                    default = true;
                    description = "Deliver only guild-channel messages that mention the bot.";
                  };
                  allowFrom = lib.mkOption {
                    type = lib.types.listOf lib.types.str;
                    default = [ ];
                    description = "Discord user IDs allowed in this guild channel; empty means anyone in the channel.";
                  };
                };
              }
            );
            default = { };
            description = "Opted-in guild channels keyed by Discord channel ID.";
          };
        };
      }
    );
    default = { };
    description = ''
      Declarative Discord plugin access allowlist per clawde agent. The access
      file is rewritten on every rebuild so it never drifts back to the empty
      default that silently drops every inbound message. Populate the
      identifiers from private-config so they stay out of the public tree.
    '';
  };

  config = lib.mkIf (discordChannelAccessByAgent != { }) {
    home.activation.deployClawdeDiscordChannelAccess = lib.hm.dag.entryAfter [ "writeBoundary" ] (
      lib.concatStringsSep "\n" (
        lib.mapAttrsToList deployAccessFileCommandFor discordChannelAccessByAgent
      )
    );
  };
}
