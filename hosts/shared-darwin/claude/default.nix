{ lib, ... }:
let
  claudeAiAccountConnectorsDisabledManagedSettings = builtins.toJSON {
    deniedMcpServers = [
      "claude_ai_Gmail"
      "claude_ai_Google_Calendar"
      "claude_ai_Google_Drive"
      "claude_ai_Claude_Code_Remote"
      "claude_ai_Context7"
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
