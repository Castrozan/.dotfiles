{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../fish.nix
    ../kitty.nix
    ../tmux.nix
    ../wezterm.nix
    ../atuin.nix
    ../yazi.nix
  ];
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
}
