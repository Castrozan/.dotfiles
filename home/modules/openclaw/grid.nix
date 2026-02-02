{
  lib,
  ...
}:
let
  gridData = import ../../../agents/grid.nix;
  telegramIdsPath = ../../../private-config/telegram-ids.nix;
  telegramIds = if builtins.pathExists telegramIdsPath then import telegramIdsPath else { };

  # Generate GRID.md members section
  gridMembersEntries = lib.concatStringsSep "\n\n" (
    lib.mapAttrsToList (
      name: agent:
      let
        capitalName = lib.toUpper (lib.substring 0 1 name) + lib.substring 1 (-1) name;
      in
      "### ${capitalName} ${agent.emoji}\n- **Role**: ${agent.role}\n- **Workspace**: ${agent.workspace}"
    ) gridData.agents
  );
in
{
  options.openclaw.gridPlaceholders = lib.mkOption {
    type = lib.types.attrsOf lib.types.str;
    internal = true;
    description = "Grid-derived placeholder values for substituteAgentConfig";
  };

  config.openclaw.gridPlaceholders = {
    "@GRID_MEMBERS@" = gridMembersEntries;
  }
  // lib.optionalAttrs (telegramIds != { }) {
    "@cleverBotId@" = telegramIds.cleverBotId or "";
    "@robsonBotId@" = telegramIds.robsonBotId or "";
    "@armadaLucasGroupId@" = telegramIds.armadaLucasGroupId or "";
  };
}
