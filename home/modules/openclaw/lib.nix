# OpenClaw library functions for multi-agent management
{ lib }:
{
  # Generate a fleet of agents from a template
  # Usage:
  #   openclaw.agents = openclawLib.mkFleet {
  #     template = { enable = true; emoji = "⚙️"; role = "worker"; model.primary = "..."; };
  #     count = 3;
  #     namePrefix = "worker";
  #     workspaceBase = "openclaw/workers";
  #   };
  # Creates: worker-1, worker-2, worker-3 with workspaces worker-1, worker-2, etc.
  mkFleet =
    {
      template,
      count,
      namePrefix,
      workspaceBase,
    }:
    lib.genAttrs (lib.genList (i: "${namePrefix}-${toString (i + 1)}") count) (
      name:
      template
      // {
        workspace = "${workspaceBase}/${name}";
      }
    );

  # Merge multiple agent sets (useful for combining fleet with named agents)
  # Usage:
  #   openclaw.agents = openclawLib.mergeAgents [
  #     { robson = { ... }; }
  #     (openclawLib.mkFleet { ... })
  #   ];
  mergeAgents = lib.foldl' (acc: agents: acc // agents) { };
}
