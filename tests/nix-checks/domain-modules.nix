{
  pkgs,
  lib,
  inputs,
}:
let
  helpers = import ./helpers.nix { inherit pkgs lib inputs; };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/yazi.nix
    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/zed-editor.nix
    ../../home/modules/browser/firefox.nix
    ../../home/modules/browser/chrome-global.nix
    ../../home/modules/desktop/fonts.nix
    ../../home/modules/desktop/fuzzel.nix
    ../../home/modules/desktop/clipse.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/bruno.nix
    ../../home/modules/dev/devenv.nix
    ../../home/modules/dev/ccost.nix
    ../../home/modules/dev/mcporter.nix
    ../../home/modules/gaming/vesktop.nix
    ../../home/modules/gaming/cbonsai.nix
    ../../home/modules/gaming/cmatrix.nix
    ../../home/modules/gaming/install-nothing.nix
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/gnome/gtk.nix
    ../../home/modules/media/ani-cli.nix
    ../../home/modules/media/bad-apple.nix
    ../../home/modules/media/youtube.nix
    ../../home/modules/media/suwayomi-server.nix
    ../../home/modules/voice/hey-bot.nix
    ../../home/modules/voice/voxtype.nix
    ../../home/modules/voice/whisp-away.nix
    ../../home/modules/voice/voice-pipeline.nix
    ../../home/modules/ollama
    ../../home/modules/network/network-optimization.nix
    ../../home/modules/network/tailscale-daemon.nix
    ../../home/modules/system/lid-switch-ignore.nix
    ../../home/modules/system/oom-protection.nix
    ../../home/modules/sourcebot
    ../../home/modules/opencode
    ../../home/modules/openclaw-mesh
    ../../home/modules/security
    ../../home/modules/testing
    ../../home/modules/audio
  ];

  fileNames = builtins.attrNames cfg.home.file;
  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;

  hasFile = name: builtins.hasAttr name cfg.home.file;
  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
  hasActivation = name: builtins.hasAttr name cfg.home.activation;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
  hasFilePrefix =
    prefix:
    builtins.length (
      builtins.filter (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames
    ) > 0;
in
{
  domain-terminal-fish-enabled =
    mkEvalCheck "domain-terminal-fish-enabled"
      (cfg.programs.fish.enable && builtins.length cfg.programs.fish.plugins >= 3)
      "fish should be enabled with >= 3 plugins, got ${toString (builtins.length cfg.programs.fish.plugins)}";

  domain-terminal-carapace-enabled =
    mkEvalCheck "domain-terminal-carapace-enabled" cfg.programs.carapace.enable
      "carapace completion should be enabled";

  domain-terminal-kitty-catppuccin =
    mkEvalCheck "domain-terminal-kitty-catppuccin"
      (cfg.programs.kitty.enable && cfg.programs.kitty.themeFile == "Catppuccin-Mocha")
      "kitty should be enabled with Catppuccin-Mocha theme, got ${
        cfg.programs.kitty.themeFile or "null"
      }";

  domain-terminal-tmux-config = mkEvalCheck "domain-terminal-tmux-config" (
    cfg.programs.tmux.enable && cfg.programs.tmux.baseIndex == 1
  ) "tmux should be enabled with baseIndex 1";

  domain-terminal-wezterm-enabled =
    mkEvalCheck "domain-terminal-wezterm-enabled" cfg.programs.wezterm.enable
      "wezterm should be enabled";

  domain-terminal-atuin-fish = mkEvalCheck "domain-terminal-atuin-fish" (
    cfg.programs.atuin.enable && cfg.programs.atuin.enableFishIntegration
  ) "atuin should be enabled with fish integration";

  domain-terminal-yazi-enabled =
    mkEvalCheck "domain-terminal-yazi-enabled" cfg.programs.yazi.enable
      "yazi file manager should be enabled";

  domain-editor-neovim-config = mkEvalCheck "domain-editor-neovim-config" (
    cfg.programs.neovim.enable && hasFile ".config/nvim"
  ) "neovim should be enabled with config directory";

  domain-browser-firefox-enabled =
    mkEvalCheck "domain-browser-firefox-enabled" cfg.programs.firefox.enable
      "firefox should be enabled";

  domain-browser-chrome-desktop-entry =
    mkEvalCheck "domain-browser-chrome-desktop-entry"
      (builtins.hasAttr "chrome-global" cfg.xdg.desktopEntries)
      "chrome desktop entry should be registered";

  domain-desktop-fontconfig-enabled =
    mkEvalCheck "domain-desktop-fontconfig-enabled" cfg.fonts.fontconfig.enable
      "fontconfig should be enabled";

  domain-desktop-fuzzel-enabled =
    mkEvalCheck "domain-desktop-fuzzel-enabled" cfg.programs.fuzzel.enable
      "fuzzel launcher should be enabled";

  domain-desktop-clipse-service-config = mkEvalCheck "domain-desktop-clipse-service-config" (
    hasService "clipse" && hasXdgConfig "clipse/config.json"
  ) "clipse should have service and config";

  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" cfg.programs.lazygit.enable
      "lazygit should be enabled";

  domain-dev-bruno-config =
    mkEvalCheck "domain-dev-bruno-config" (hasXdgConfig "bruno/preferences.json")
      "bruno config should be deployed";

  domain-dev-devenv-package =
    mkEvalCheck "domain-dev-devenv-package" (hasPackageMatching ".*devenv.*")
      "devenv package should be installed";

  domain-gaming-vesktop-config =
    mkEvalCheck "domain-gaming-vesktop-config" (hasFile ".config/vesktop/settings/settings.json")
      "vesktop config should be deployed";

  domain-gnome-gtk-enabled =
    mkEvalCheck "domain-gnome-gtk-enabled" cfg.gtk.enable
      "gtk theming should be enabled";

  domain-gnome-dconf-settings =
    mkEvalCheck "domain-gnome-dconf-settings"
      (builtins.hasAttr "org/gnome/desktop/interface" cfg.dconf.settings)
      "dconf settings should be configured";

  domain-security-gpg-agent = mkEvalCheck "domain-security-gpg-agent" (
    cfg.programs.gpg.enable && cfg.services.gpg-agent.enable
  ) "gpg and gpg-agent should be enabled";

  domain-security-password-store = mkEvalCheck "domain-security-password-store" (
    cfg.programs.password-store.enable && hasService "password-store-git-sync"
  ) "password-store should be enabled with sync service";

  domain-security-agenix-secrets = mkEvalCheck "domain-security-agenix-secrets" (
    builtins.length (builtins.attrNames cfg.age.secrets) > 0 && hasFile ".secrets/source-secrets.sh"
  ) "agenix secrets should be configured";

  domain-ollama-service-binary = mkEvalCheck "domain-ollama-service-binary" (
    hasService "ollama" && hasFile ".local/bin/ollama"
  ) "ollama should have service and binary";

  domain-opencode-package =
    mkEvalCheck "domain-opencode-package" (hasPackageMatching ".*opencode.*")
      "opencode package should be installed";

  domain-openclaw-mesh-config = mkEvalCheck "domain-openclaw-mesh-config" (
    hasXdgConfig "openclaw-mesh/config.json" && builtins.hasAttr "mesh" cfg.openclaw
  ) "openclaw-mesh should have config and options";

  domain-audio-bluetooth-service =
    mkEvalCheck "domain-audio-bluetooth-service" (hasService "bluetooth-audio-autoswitch")
      "bluetooth audio autoswitch service should exist";

  domain-system-network-optimization =
    mkEvalCheck "domain-system-network-optimization" (hasActivation "setupNetworkOptimization")
      "network optimization activation should exist";

  domain-system-oom-protection =
    mkEvalCheck "domain-system-oom-protection" (hasActivation "setupOomProtection")
      "oom protection activation should exist";

  domain-system-lid-switch =
    mkEvalCheck "domain-system-lid-switch" (hasActivation "setupLidSwitchIgnore")
      "lid switch ignore activation should exist";

  domain-voice-hey-bot-options =
    mkEvalCheck "domain-voice-hey-bot-options" (builtins.hasAttr "hey-bot" cfg.services)
      "hey-bot options should be declared";

  domain-sourcebot-package =
    mkEvalCheck "domain-sourcebot-package" (hasPackageMatching ".*sourcebot.*")
      "sourcebot package should be installed";
}
