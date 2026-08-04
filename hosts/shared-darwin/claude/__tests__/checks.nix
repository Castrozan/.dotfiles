{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  claudeDarwinPolicyConfig = import ../default.nix { inherit lib; };

  managedSettingsInstallScript =
    claudeDarwinPolicyConfig.system.activationScripts.postActivation.text.content;

  claudeAiAccountConnectorsDeniedByManagedSettings =
    lib.hasInfix "/Library/Application Support/ClaudeCode/managed-settings.json" managedSettingsInstallScript
    && lib.hasInfix "deniedMcpServers" managedSettingsInstallScript
    && lib.hasInfix "serverName" managedSettingsInstallScript
    && lib.hasInfix "claude.ai Gmail" managedSettingsInstallScript
    && lib.hasInfix "claude.ai Google Calendar" managedSettingsInstallScript
    && lib.hasInfix "claude.ai Google Drive" managedSettingsInstallScript
    && lib.hasInfix "claude.ai Claude Code Remote" managedSettingsInstallScript
    && lib.hasInfix "claude.ai Context7" managedSettingsInstallScript;
in
{
  macbook-claude-ai-account-connectors-disabled =
    mkEvalCheck "macbook-claude-ai-account-connectors-disabled"
      claudeAiAccountConnectorsDeniedByManagedSettings
      "Claude Code must deploy a system managed-settings.json listing all five claude.ai account connectors (Gmail, Google Calendar, Google Drive, Claude Code Remote, Context7) in deniedMcpServers, the only surface that suppresses subscription-synced connectors since user and project settings cannot override managed keys; each entry MUST be a { serverName = <verbatim display name>; } object (the deniedMcpServers schema is an array of objects with exactly one of serverName/serverCommand/serverUrl, so a bare string array fails validation and Claude Code drops the whole array), and the names must match the claudeAiMcpEverConnected memos verbatim; without it the connectors reload their MCP tool prefix into every interactive session";
}
