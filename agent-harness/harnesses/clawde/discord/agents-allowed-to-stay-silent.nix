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
      here empties that one Stop hook in its own workspace settings and leaves
      every other hook in place, because the pre-tool-use prohibited-command guard
      that denies an agent destructive commands is a hook too and a character
      reachable by strangers is exactly the agent that must keep it. Its tool
      restrictions are untouched as well, since those are permissions.deny entries
      the harness enforces itself rather than hooks.
    '';
  };

  config = {
    clawde.channelAdapters.discord.workspaceSettingsFor =
      { name, ... }:
      lib.optionalAttrs (builtins.elem name agentsAllowedToStaySilent) {
        hooks.Stop = lib.mkForce [ ];
      };
  };
}
