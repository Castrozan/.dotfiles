{
  pkgs,
  lib,
  mkEvalCheck,
  helpers,
  self,
  ...
}:
let
  claudeModsMarketplace = import ../marketplace.nix { inherit pkgs; };

  cfg = helpers.homeManagerTestConfiguration [ self.homeManagerModules.claude-code ];

  userSettingsEnabledPlugins =
    (builtins.fromJSON cfg.home.file.".claude/settings.json.nix-source".source.baseSettings.text)
    .enabledPlugins;

  installActivation = cfg.home.activation.installClaudeMods;
in
{
  claude-interactive-only-mods-stay-out-of-user-settings =
    mkEvalCheck "claude-interactive-only-mods-stay-out-of-user-settings"
      (
        !lib.any (pluginKey: userSettingsEnabledPlugins ? ${pluginKey}) (
          builtins.attrNames claudeModsMarketplace.interactiveSessionEnabledPlugins
        )
      )
      "user settings reach every Claude process, including clawde agents that launch the unwrapped binary; an interactive-only mod enabled there would send keep-warm pings, hold channel messages, or rewrite prompts in fleet sessions nobody is watching, so only the interactive wrapper's --settings file may enable these";

  claude-compaction-brief-reaches-every-session =
    mkEvalCheck "claude-compaction-brief-reaches-every-session"
      (userSettingsEnabledPlugins."compaction-brief@dotfiles-mods" or false)
      "the compaction brief steers what every summary keeps, and fleet agents compact as often as interactive sessions do, so it must be enabled in user settings rather than through the interactive wrapper";

  claude-mods-install-before-settings-seeding =
    mkEvalCheck "claude-mods-install-before-settings-seeding"
      (
        builtins.elem "seedClaudeSettingsAsMutableFile" installActivation.before
        && builtins.all (
          pluginKey: lib.hasInfix "plugin install ${pluginKey}" installActivation.data
        ) claudeModsMarketplace.pluginKeys
      )
      "claude plugin install writes each mod into settings.json as enabled; only the settings seeding that runs afterwards resets enabledPlugins to the nix source, so installing after it would leave every interactive-only mod enabled for clawde agents until the next rebuild";
}
