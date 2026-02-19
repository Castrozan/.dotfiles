{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  capitalize = s: lib.toUpper (lib.substring 0 1 s) + lib.substring 1 (-1) s;

  gridMembersEntries = lib.concatStringsSep "\n\n" (
    lib.mapAttrsToList (
      name: agent:
      "### ${capitalize name} ${agent.emoji}\n- **Role**: ${agent.role}\n- **Workspace**: ~/${agent.workspace}"
    ) openclaw.enabledAgents
  );

  workspacePaths = lib.concatStringsSep " " (
    map (agentName: "\"${homeDir}/${openclaw.agents.${agentName}.workspace}\"") (
      lib.attrNames openclaw.enabledAgents
    )
  );

  substituteScript = pkgs.writeShellScript "substitute-telegram-ids" ''
    set -euo pipefail
    IDS="/run/agenix/telegram-ids"

    [ -f "$IDS" ] || exit 0

    for WORKSPACE in ${workspacePaths}; do
      [ -d "$WORKSPACE" ] || continue
      while IFS='=' read -r key value; do
        [ -n "$key" ] || continue
        ${pkgs.findutils}/bin/find "$WORKSPACE" -name "*.md" \
          -exec ${pkgs.gnused}/bin/sed -i "s/@''${key}@/''${value}/g" {} +
      done < "$IDS"
    done
  '';

  telegramIdsSecretExists = builtins.pathExists ../../../secrets/telegram-ids.age;
in
{
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
