{
  pkgs,
  hostname,
  config,
  ...
}:
let
  perMachineLauncherSpecsPath =
    ../../../private-config/machines + "/${hostname}/claude/config-dir-launchers.nix";
  perMachineLauncherSpecs =
    if builtins.pathExists perMachineLauncherSpecsPath then import perMachineLauncherSpecsPath else [ ];

  seedConfigDirOverlayScript = ./scripts/seed-claude-config-dir-overlay;

  buildIsolatedConfigDirLauncher =
    launcherSpec:
    let
      settingsOverlayFile = pkgs.writeText "${launcherSpec.name}-settings-overlay.json" (
        builtins.toJSON launcherSpec.settingsOverlay
      );
    in
    pkgs.writeShellScriptBin launcherSpec.name ''
      export CLAUDE_CONFIG_DIR="$HOME/${launcherSpec.configDirectoryName}"
      export CLAUDE_SECURESTORAGE_CONFIG_DIR=""
      ${pkgs.python312}/bin/python3 ${seedConfigDirOverlayScript} \
        --source-config-directory "$HOME/.claude" \
        --target-config-directory "$CLAUDE_CONFIG_DIR" \
        --settings-overlay-file ${settingsOverlayFile} || true
      exec ${config.claude.package}/bin/claude "$@"
    '';
in
{
  home.packages = map buildIsolatedConfigDirLauncher perMachineLauncherSpecs;
}
