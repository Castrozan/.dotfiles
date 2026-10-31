{
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  cfg = helpers.homeManagerTestConfiguration [ self.homeManagerModules.claude-code ];

  userSettingsEnabledPlugins =
    (builtins.fromJSON cfg.home.file.".claude/settings.json.nix-source".source.baseSettings.text)
    .enabledPlugins;

  interactiveLauncher = builtins.readFile "${cfg.claude.package}/bin/claude";

  retirementActivation = cfg.home.activation.removeRetiredClaudeMarketplaces;
in
{
  claude-dotfiles-is-the-only-enabled-plugin =
    mkEvalCheck "claude-dotfiles-is-the-only-enabled-plugin"
      (
        userSettingsEnabledPlugins == {
          "dotfiles@dotagents" = true;
        }
      )
      "user settings reach every Claude process, including clawde agents that launch the unwrapped binary; the compaction brief travels inside the dotfiles plugin, and an interactive mod enabled there would send keep-warm pings, hold channel messages, or rewrite prompts in fleet sessions nobody is watching";

  claude-interactive-launcher-loads-the-mods-directory =
    mkEvalCheck "claude-interactive-launcher-loads-the-mods-directory"
      (lib.hasInfix "--plugin-dir ${builtins.unsafeDiscardStringContext cfg.claude.interactiveSessionModsDirectory}" interactiveLauncher)
      "the interactive mods have no marketplace, so the launcher flag is the only thing that loads them into a keyboard session";

  claude-interactive-settings-enable-no-plugin =
    mkEvalCheck "claude-interactive-settings-enable-no-plugin"
      (
        !(cfg.claude.interactiveSessionSettings ? enabledPlugins)
        && cfg.claude.interactiveSessionSettings.pluginConfigs ? "airquote@inline"
      )
      "mods loaded with --plugin-dir read their options under the inline plugin key and need no enablement";

  claude-retired-marketplaces-go-before-settings-seeding =
    mkEvalCheck "claude-retired-marketplaces-go-before-settings-seeding"
      (builtins.elem "seedClaudeSettingsAsMutableFile" retirementActivation.before)
      "removing a marketplace rewrites settings.json, so only the seeding that runs afterwards leaves it matching the nix source";
}
