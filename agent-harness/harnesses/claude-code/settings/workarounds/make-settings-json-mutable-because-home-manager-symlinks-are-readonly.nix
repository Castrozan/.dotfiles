{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  verifyDeployedProhibitedWordsAllowlist = import ./verify-deployed-prohibited-words-allowlist.nix {
    inherit pkgs;
  };
in
{
  home.activation = {
    seedClaudeSettingsAsMutableFile = {
      after = [ "writeBoundary" ];
      before = [ ];
      data = ''
        export CLAUDE_SETTINGS="$HOME/.claude/settings.json"
        export NIX_SOURCE="$HOME/.claude/settings.json.nix-source"
        export JQ_BIN=${pkgs.jq}/bin/jq
        ${pkgs.bash}/bin/bash ${./seed-claude-settings-mutable.sh}
      '';
    };

    verifyDeployedProhibitedWordsAllowlist = {
      after = [ "seedClaudeSettingsAsMutableFile" ];
      before = [ ];
      data = ''
        ${verifyDeployedProhibitedWordsAllowlist}/bin/verify-deployed-prohibited-words-allowlist "$HOME/.dotfiles" ${lib.escapeShellArg hostname}
      '';
    };
  };
}
