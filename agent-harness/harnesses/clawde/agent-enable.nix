{ lib, ... }:
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options.enable = lib.mkOption {
          type = lib.types.bool;
          default = true;
          description = ''
            Whether this agent belongs to the live fleet. False keeps the declaration
            in the tree and removes the agent from config.clawde.agents before any
            consumer reads it, so the supervisor spawns no window, no Discord sidecar,
            no heartbeat and no health probe for it, and nothing may look it up by
            name while it is off. onDemand keeps a service-lifetime channel bridge
            connected so an operator or a message can start the agent; a disabled
            agent holds nothing until it is enabled again.
          '';
        };
      }
    );
    apply = lib.filterAttrs (_: agent: agent.enable);
  };
}
