{
  config,
  lib,
  ...
}:
let
  agentsDeniedDestructiveCommands = config.clawdeAgentsDeniedDestructiveCommands;
  agentsAllowedToStaySilent = config.clawdeDiscordAgentsAllowedToStaySilent;

  harnessesReachableBy =
    agentName:
    let
      agent = config.clawde.agents.${agentName} or null;
    in
    if agent == null then [ ] else [ agent.harness ] ++ agent.harnessFallbackChain;

  agentsWhoseDenialHooksAreSwitchedOff = lib.filter (
    agentName:
    lib.elem agentName agentsAllowedToStaySilent && lib.elem "claude" (harnessesReachableBy agentName)
  ) agentsDeniedDestructiveCommands;
in
{
  options.clawdeAgentsDeniedDestructiveCommands = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
    description = ''
      Clawde agents whose turns must never run a destructive system command,
      named one entry each. Codex cannot enforce a call-time permissions.deny
      entry the way claude does, so an agent moved onto it silently loses every
      Bash deny its claude configuration carried; a channel agent reachable from
      Discord then answers strangers with unrestricted shell. The pre-tool-use
      prohibited-command guard reads this list and denies sudo, rm, dd, mkfs,
      fdisk, shutdown, reboot, halt and poweroff for a named agent on every
      harness, which is enforcement the harness itself cannot be asked for.

      An agent is matched by the CLAWDE_AGENT_NAME its wrapper exports, so the
      denial follows the agent across harnesses and reaches its channel bridge
      turns as well as its own window. Interactive human sessions export no such
      name and are never restricted.
    '';
  };

  config = {
    assertions = [
      {
        assertion = agentsWhoseDenialHooksAreSwitchedOff == [ ];
        message = ''
          clawde: ${lib.concatStringsSep ", " agentsWhoseDenialHooksAreSwitchedOff} may
          reach the claude harness while named in both clawdeAgentsDeniedDestructiveCommands
          and clawdeDiscordAgentsAllowedToStaySilent. Staying silent is bought with
          disableAllHooks in the agent's own workspace settings, which switches off the
          pre-tool-use guard that carries the destructive-command denial, so on claude the
          agent would run sudo and rm with nothing left to stop it. Drop claude from the
          agent's harness and harnessFallbackChain, or drop one of the two lists.
        '';
      }
    ];

    home.file."clawde/agents-denied-destructive-commands.json".text =
      builtins.toJSON agentsDeniedDestructiveCommands;
  };
}
