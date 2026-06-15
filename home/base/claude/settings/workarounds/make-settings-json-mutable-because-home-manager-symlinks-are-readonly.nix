{ pkgs, ... }:
{
  home.activation.seedClaudeSettingsAsMutableFile = {
    after = [ "writeBoundary" ];
    before = [ ];
    data = ''
      export CLAUDE_SETTINGS="$HOME/.claude/settings.json"
      export NIX_SOURCE="$HOME/.claude/settings.json.nix-source"
      export JQ_BIN=${pkgs.jq}/bin/jq
      ${pkgs.bash}/bin/bash ${./seed-claude-settings-mutable.sh}
    '';
  };
}
