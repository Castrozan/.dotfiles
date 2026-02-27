# Workaround: no global setting to skip workspace trust dialog yet.
# Track: https://github.com/anthropics/claude-code/issues/23109
# When implemented, replace this with a trustedWorkspacePatterns setting.
{ pkgs, ... }:
let
  trustedParentDirectories = [
    "$HOME/repo"
    "$HOME/betha-fly/projects"
  ];

  trustedDirectories = [
    "$HOME"
    "$HOME/.dotfiles"
  ];

  trustDirectoryJqFilter = ".projects[$path].hasTrustDialogAccepted = true";

  trustChildrenScript = builtins.concatStringsSep "\n" (
    map (dir: ''
      if [ -d "${dir}" ]; then
        for d in "${dir}"/*/; do
          d="''${d%/}"
          [ -d "$d" ] && $JQ --arg path "$d" '${trustDirectoryJqFilter}' "$F" > "$F.tmp" && mv "$F.tmp" "$F"
        done
      fi
    '') trustedParentDirectories
  );

  trustExplicitScript = builtins.concatStringsSep "\n" (
    map (dir: ''
      $JQ --arg path "${dir}" '${trustDirectoryJqFilter}' "$F" > "$F.tmp" && mv "$F.tmp" "$F"
    '') trustedDirectories
  );
in
{
  home.activation.trustAllWorkspacesForClaude = {
    after = [ "patchClaudeJsonInstallMethod" ];
    before = [ ];
    data = ''
      F="$HOME/.claude.json"
      JQ="${pkgs.jq}/bin/jq"
      [ -f "$F" ] || exit 0
      ${trustChildrenScript}
      ${trustExplicitScript}
    '';
  };
}
