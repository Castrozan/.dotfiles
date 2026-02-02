{
  config,
  lib,
  ...
}:
let
  openclaw = config.openclaw;
  gridData = import ../../../agents/grid.nix;

  # Generate GRID_HOSTS bash associative array entries: [name]="host:port"
  gridHostsEntries = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (
      name: agent: "  [${name}]=\"${agent.host}:${toString agent.port}\""
    ) gridData.agents
  );
  gridHostsBash = "declare -A GRID_HOSTS=(\n${gridHostsEntries}\n)";

  # Generate GRID.md members section (no network details)
  gridMembersEntries = lib.concatStringsSep "\n\n" (
    lib.mapAttrsToList (
      name: agent:
      let
        capitalName = lib.toUpper (lib.substring 0 1 name) + lib.substring 1 (-1) name;
      in
      "### ${capitalName} ${agent.emoji}\n- **Role**: ${agent.role}\n- **Workspace**: ${agent.workspace}"
    ) gridData.agents
  );

  capitalize = name: lib.toUpper (lib.substring 0 1 name) + lib.substring 1 (-1) name;

  # Generate health check blocks for remote agents only (excludes current agent)
  remoteAgents = lib.filterAttrs (name: _: name != openclaw.agent) gridData.agents;
  gridHealthChecks = lib.concatStringsSep "\n" (
    lib.mapAttrsToList (name: agent: ''
      echo -e "''${BOLD}${capitalize name}''${NC}"
      if curl -sf --connect-timeout 3 http://${agent.host}:${toString agent.port}/health >/dev/null 2>&1; then
        ok "${capitalize name} gateway responding (port ${toString agent.port})"
      else
        warn "${capitalize name} gateway unreachable (machine may be off)"
      fi'') remoteAgents
  );
in
{
  options.openclaw.gridPlaceholders = lib.mkOption {
    type = lib.types.attrsOf lib.types.str;
    internal = true;
    description = "Grid-derived placeholder values for substituteAgentConfig";
  };

  config.openclaw.gridPlaceholders = {
    "@GRID_HOSTS@" = gridHostsBash;
    "@GRID_MEMBERS@" = gridMembersEntries;
    "@GRID_HEALTH_CHECKS@" = gridHealthChecks;
  };
}
