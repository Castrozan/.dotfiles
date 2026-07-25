{ lib, ... }:
let
  claudeAiAccountConnectorsDisabledManagedSettings = builtins.toJSON {
    deniedMcpServers = [
      "claude.ai Gmail"
      "claude.ai Google Calendar"
      "claude.ai Google Drive"
      "claude.ai Claude Code Remote"
      "claude.ai Context7"
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
