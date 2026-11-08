{
  config,
  lib,
  pkgs,
  inputs,
  isDarwin,
  ...
}:
let
  delta = import ./delta-package.nix { inherit pkgs inputs; };
  dotfilesCheckout = "${config.home.homeDirectory}/.dotfiles";
  claudeCommand = "${config.claude.unwrappedPackage}/bin/claude";
  claudeConfigDirectory = "${config.home.homeDirectory}/.claude";

  deltaInstallLocation =
    if isDarwin then
      { "Applications/Delta.app".source = "${delta.package}/Applications/Delta.app"; }
    else
      { ".local/delta.app/bin/delta".source = delta.commandLine; };
in
{
  home.file = deltaInstallLocation;

  home.packages = [
    (pkgs.writeShellScriptBin "zed-delta" ''exec ${delta.commandLine} "$@"'')
  ];

  home.activation.enableDeltaPluginInDotfilesCheckout =
    lib.hm.dag.entryAfter
      [
        "linkGeneration"
        "seedClaudeSettingsAsMutableFile"
      ]
      ''
        if [ -d "${dotfilesCheckout}/.git" ]; then
          if ! (
            cd "${dotfilesCheckout}" &&
              CLAUDE_CONFIG_DIR="${claudeConfigDirectory}" ${claudeCommand} plugin marketplace add zed-industries/delta-claude --scope local &&
              CLAUDE_CONFIG_DIR="${claudeConfigDirectory}" ${claudeCommand} plugin install delta@zed-industries --scope local &&
              CLAUDE_CONFIG_DIR="${claudeConfigDirectory}" ${claudeCommand} plugin update delta@zed-industries --scope local
          ); then
            echo "warning: could not enable the Delta plugin in ${dotfilesCheckout}" >&2
          fi
        fi
      '';
}
