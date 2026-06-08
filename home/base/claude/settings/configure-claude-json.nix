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
  home.activation.configureClaudeJson = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      export TRUSTED_PARENT_DIRECTORIES=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedParentDirectories)}
      export TRUSTED_DIRECTORIES=${lib.escapeShellArg (lib.concatStringsSep "\n" trustedDirectories)}
      export JQ_BIN=${pkgs.jq}/bin/jq
      ${pkgs.bash}/bin/bash ${./configure-claude-json.sh}
    '';
  };
}
