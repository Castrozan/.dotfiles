{ lib, ... }:
let
  claudeAiAccountConnectorsDisabledManagedSettings = builtins.toJSON {
    deniedMcpServers = [
      { serverName = "claude.ai Gmail"; }
      { serverName = "claude.ai Google Calendar"; }
      { serverName = "claude.ai Google Drive"; }
      { serverName = "claude.ai Claude Code Remote"; }
      { serverName = "claude.ai Context7"; }
    ];
  };
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    /bin/mkdir -p "/Library/Application Support/ClaudeCode"
    printf '%s' ${lib.escapeShellArg claudeAiAccountConnectorsDisabledManagedSettings} > "/Library/Application Support/ClaudeCode/managed-settings.json"
    /bin/chmod 0644 "/Library/Application Support/ClaudeCode/managed-settings.json"
  '';
}
