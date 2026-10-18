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

  userSettings = builtins.fromJSON (
    (helpers.homeManagerTestConfiguration [ self.homeManagerModules.claude-code ])
    .home.file.".claude/settings.json.nix-source".source.baseSettings.text
  );
in
{
  claude-ai-connectors-disabled-from-user-settings =
    mkEvalCheck "claude-ai-connectors-disabled-from-user-settings"
      (userSettings.disableClaudeAiConnectors or false)
      "disableClaudeAiConnectors in user settings keeps every claude.ai account connector from loading its MCP tool prefix into each session on every host, without a managed-settings.json; any managed settings file loads Claude Code's built-in sec-default guard, which skips every user mod on classic.* and prompt.compose events and so silently disables Cache Tax's resume warning and crayon's model teaching";

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
