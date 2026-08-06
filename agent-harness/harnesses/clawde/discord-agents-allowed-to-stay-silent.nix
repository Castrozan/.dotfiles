{
  config,
  lib,
  ...
}:
let
  agentsAllowedToStaySilent = config.clawdeDiscordAgentsAllowedToStaySilent;
in
{
  options.clawdeDiscordAgentsAllowedToStaySilent = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
    description = ''
      Discord clawde agents whose design lets a turn end with nothing sent, named
      one entry each. The Discord channel adapter installs a Stop hook that blocks
      every turn ending without a call to the reply tool and orders the agent to
      send its answer, which is right for an assistant answering its owner and
      wrong for a character who decides when to speak: each deliberate silence
      comes back out as a filler message in the channel, so a bot that should be
      quiet posts a placeholder after every line anyone writes. Naming an agent
      here writes disableAllHooks into its own workspace settings, switching off
      every hook that reaches it, the adapter's reply enforcement and the
      machine-tier developer hooks alike, none of which a conversational agent has
      any use for. Its tool restrictions are untouched, since those are
      permissions.deny entries the harness enforces itself rather than hooks.
    '';
  };

  config = {
    clawde.channelAdapters.discord.workspaceSettingsFor =
      { name, ... }:
      lib.optionalAttrs (builtins.elem name agentsAllowedToStaySilent) {
        disableAllHooks = true;
      };
  };
}
