{
  pkgs,
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

  avatarPluginRoot = cfg.agentPlugins.avatarPlugin;
  avatarClaudeManifest = builtins.fromJSON (
    builtins.readFile "${avatarPluginRoot}/.claude-plugin/plugin.json"
  );
  avatarPluginCarriesOnlySkills =
    builtins.all (
      key:
      builtins.elem key [
        "name"
        "description"
        "version"
        "license"
        "repository"
        "homepage"
        "keywords"
        "author"
        "skills"
      ]
    ) (builtins.attrNames avatarClaudeManifest)
    && !(builtins.any (component: builtins.pathExists "${avatarPluginRoot}/${component}") [
      "hooks"
      "commands"
      "agents"
      "output-styles"
      ".mcp.json"
      ".lsp.json"
    ]);

  interactiveLauncher = builtins.readFile "${cfg.claude.package}/bin/claude";

  retirementActivation = cfg.home.activation.removeRetiredClaudeMarketplaces;

  hostInteractiveSessionModsDirectory =
    (import ../. { inherit pkgs; }).interactiveSessionModsDirectory;
in
{
  claude-user-settings-enable-no-interactive-mod =
    mkEvalCheck "claude-user-settings-enable-no-interactive-mod"
      (
        userSettingsEnabledPlugins == {
          "dotfiles@dotagents" = true;
          "avatar@avatar" = true;
        }
        && avatarPluginCarriesOnlySkills
      )
      "user settings reach every Claude process, including clawde agents that launch the unwrapped binary, so they enable only the dotfiles plugin and the avatar plugin, which may carry nothing but skills; the compaction brief travels inside the dotfiles plugin, and an interactive mod enabled there would send keep-warm pings, hold channel messages, or rewrite prompts in fleet sessions nobody is watching";

  claude-interactive-launcher-loads-the-mods-directory =
    mkEvalCheck "claude-interactive-launcher-loads-the-mods-directory"
      (lib.hasInfix "--plugin-dir ${builtins.unsafeDiscardStringContext cfg.claude.interactiveSessionModsDirectory}" interactiveLauncher)
      "the interactive mods have no marketplace, so the launcher flag is the only thing that loads them into a keyboard session";

  claude-cache-tax-writes-no-transcript-messages =
    pkgs.runCommandLocal "claude-cache-tax-writes-no-transcript-messages" { }
      ''
        ! grep -n '$.ui.log(' ${hostInteractiveSessionModsDirectory}/cache-tax/hooks/register.ts
        touch "$out"
      '';

  claude-crayon-leaves-first-fullscreen-draw-to-engine =
    pkgs.runCommandLocal "claude-crayon-leaves-first-fullscreen-draw-to-engine" { }
      ''
        grep -n 'props: { onScreen: \[null, { of: ' ${hostInteractiveSessionModsDirectory}/crayon/hooks/register.tsx
        touch "$out"
      '';

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
