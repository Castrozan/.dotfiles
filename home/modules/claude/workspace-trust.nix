{
  pkgs,
  config,
  lib,
  ...
}:
let
  trustedParentDirectories = [
    "${config.home.homeDirectory}/repo"
  ];

  trustedDirectories = [
    "${config.home.homeDirectory}"
    "${config.home.homeDirectory}/.dotfiles"
  ];
in
{
  home.activation.trustAllWorkspacesForClaude = {
    after = [ "patchClaudeJsonInstallMethod" ];
    before = [ ];
    data = ''
      export TRUSTED_PARENT_DIRS=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedParentDirectories)}
      export TRUSTED_DIRS=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedDirectories)}
      export JQ_BIN=${pkgs.jq}/bin/jq
      ${builtins.readFile ./scripts/trust-claude-workspaces.sh}
    '';
  };
}
