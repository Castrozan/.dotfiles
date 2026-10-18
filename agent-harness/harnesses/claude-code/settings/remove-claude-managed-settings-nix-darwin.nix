{ pkgs, ... }:
let
  managedSettingsPath = "/Library/Application Support/ClaudeCode/managed-settings.json";

  managedSettingsThisRepositoryOnceWrote =
    pkgs.writeText "claude-managed-settings-this-repository-once-wrote.json"
      (
        builtins.toJSON {
          deniedMcpServers = [
            { serverName = "claude.ai Gmail"; }
            { serverName = "claude.ai Google Calendar"; }
            { serverName = "claude.ai Google Drive"; }
            { serverName = "claude.ai Claude Code Remote"; }
            { serverName = "claude.ai Context7"; }
          ];
        }
      );
in
{
  system.activationScripts.postActivation.text = pkgs.lib.mkAfter ''
    if /usr/bin/cmp -s ${managedSettingsThisRepositoryOnceWrote} ${pkgs.lib.escapeShellArg managedSettingsPath}; then
      /bin/rm -f ${pkgs.lib.escapeShellArg managedSettingsPath}
    fi
  '';
}
