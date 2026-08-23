{
  config,
  lib,
  ...
}:
let
  agentsDeniedDestructiveCommands = config.clawdeAgentsDeniedDestructiveCommands;
in
{
  options.clawdeAgentsDeniedDestructiveCommands = lib.mkOption {
    type = lib.types.listOf lib.types.str;
    default = [ ];
    description = ''
      Clawde agents whose turns must never run a destructive system command,
      named one entry each. A harness that enforces no call-time tool deny, as
      codex does not, silently drops every Bash deny an agent's configuration
      carried the moment the agent moves onto it, and a channel agent reachable
      from Discord then answers strangers with unrestricted shell. The
      pre-tool-use prohibited-command guard reads this list and denies sudo, rm,
      dd, mkfs, fdisk, shutdown, reboot, halt and poweroff for a named agent, so
      the denial holds wherever the guard runs rather than only where a harness
      happens to implement tool denies itself.

      An agent is matched by the CLAWDE_AGENT_NAME its wrapper exports, so the
      denial follows the agent across harnesses and reaches its channel bridge
      turns as well as its own window. Interactive human sessions export no such
      name and are never restricted.
    '';
  };

  config.home.file."clawde/agents-denied-destructive-commands.json".text =
    builtins.toJSON agentsDeniedDestructiveCommands;
}
