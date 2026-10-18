{
  helpers,
  pkgs,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  managedSettingsRemovalScript =
    (import ../settings/remove-claude-managed-settings-nix-darwin.nix { inherit pkgs; })
    .system.activationScripts.postActivation.text.content;

  claudeConfiguration = helpers.homeManagerTestConfiguration [ self.homeManagerModules.claude-code ];

  userSettings =
    builtins.fromJSON
      claudeConfiguration.home.file.".claude/settings.json.nix-source".source.baseSettings.text;
in
{
  claude-ai-account-connectors-denied-from-user-settings =
    mkEvalCheck "claude-ai-account-connectors-denied-from-user-settings"
      (
        builtins.all
          (connectorName: builtins.elem { serverName = connectorName; } userSettings.deniedMcpServers)
          [
            "claude.ai Gmail"
            "claude.ai Google Calendar"
            "claude.ai Google Drive"
            "claude.ai Claude Code Remote"
            "claude.ai Context7"
          ]
        && !(userSettings ? disableClaudeAiConnectors)
      )
      "deniedMcpServers merges from every settings file, so user settings keep these five claude.ai account connectors from loading their MCP tool prefix into each session without a managed-settings.json, whose mere presence loads Claude Code's built-in sec-default guard and makes it skip every user mod on classic.* and prompt.compose events, silently disabling Cache Tax's resume warning and crayon's model teaching; each entry must stay a { serverName = <verbatim display name>; } object, and disableClaudeAiConnectors must stay off because it would also drop the connectors that are wanted, such as Claude Docs";

  darwin-removes-only-the-managed-settings-this-repository-wrote =
    mkEvalCheck "darwin-removes-only-the-managed-settings-this-repository-wrote"
      (
        lib.hasInfix "/usr/bin/cmp -s" managedSettingsRemovalScript
        && lib.hasInfix "/Library/Application Support/ClaudeCode/managed-settings.json" managedSettingsRemovalScript
        && lib.hasInfix "/bin/rm -f" managedSettingsRemovalScript
        && !(lib.hasInfix "printf" managedSettingsRemovalScript)
      )
      "a managed-settings.json left behind keeps the sec-default guard loaded, while one written by an administrator or another tool is not ours to delete, so activation removes the file only when it matches byte for byte what this repository used to write";
}
