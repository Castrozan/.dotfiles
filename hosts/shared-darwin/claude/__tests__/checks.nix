{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  claudeDarwinPolicyConfig = import ../default.nix { inherit lib; };

  managedSettingsInstallScript =
    claudeDarwinPolicyConfig.system.activationScripts.postActivation.text.content;

  claudeAiAccountConnectorsDeniedByManagedSettings =
    lib.hasInfix "/Library/Application Support/ClaudeCode/managed-settings.json" managedSettingsInstallScript
    && lib.hasInfix "deniedMcpServers" managedSettingsInstallScript
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
      "Claude Code must deploy a system managed-settings.json listing all five claude.ai account connectors (Gmail, Google Calendar, Google Drive, Claude Code Remote, Context7) in deniedMcpServers, the only surface that suppresses subscription-synced connectors since user and project settings cannot override managed keys; without it the connectors reload their MCP tool prefix into every interactive session";
}
