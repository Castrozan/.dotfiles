{
  lib,
  pkgs,
  config,
  ...
}:
let
  gridData = import ../../../agents/grid.nix;
  inherit (config) openclaw;

  gridMembersEntries = lib.concatStringsSep "\n\n" (
    lib.mapAttrsToList (
      name: agent:
      let
        capitalName = lib.toUpper (lib.substring 0 1 name) + lib.substring 1 (-1) name;
      in
      "### ${capitalName} ${agent.emoji}\n- **Role**: ${agent.role}\n- **Workspace**: ${agent.workspace}"
    ) gridData.agents
  );

  telegramIdsSecretExists = builtins.pathExists ../../../secrets/telegram-ids.age;

  substituteScript = pkgs.writeShellScript "substitute-telegram-ids" ''
    set -euo pipefail
    IDS="/run/agenix/telegram-ids"
    WORKSPACE="${config.home.homeDirectory}/${openclaw.workspacePath}"

    [ -f "$IDS" ] || exit 0
    [ -d "$WORKSPACE" ] || exit 0

    while IFS='=' read -r key value; do
      [ -n "$key" ] || continue
      ${pkgs.findutils}/bin/find "$WORKSPACE" -name "*.md" \
        -exec ${pkgs.gnused}/bin/sed -i "s/@''${key}@/''${value}/g" {} +
    done < "$IDS"
  '';
in
{
  options.openclaw.gridPlaceholders = lib.mkOption {
    type = lib.types.attrsOf lib.types.str;
    internal = true;
    description = "Grid-derived placeholder values for substituteAgentConfig";
  };

  config = {
    openclaw.gridPlaceholders = {
      "@GRID_MEMBERS@" = gridMembersEntries;
    };

    # Telegram IDs are agenix secrets — substitute at activation time
    home.activation.substituteTelegramIds = lib.mkIf telegramIdsSecretExists (
      lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run ${substituteScript}
      ''
    );
  };
}
