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
    ../bash.nix
    ../herdr.nix
    ../kitty.nix
    ../tmux.nix
    ../wezterm.nix
    ../yazi
  ];

  herdrAutostartContent = builtins.readFile ../shell/bash_herdr_autostart.sh;
  herdrAutostartDefinesStartAndGuardsAgainstNestingAndTmux =
    lib.hasInfix "_start_herdr()" herdrAutostartContent
    && lib.hasInfix "HERDR_ENV" herdrAutostartContent
    && lib.hasInfix "\${TMUX:-}" herdrAutostartContent
    && lib.hasInfix "command -v herdr" herdrAutostartContent;
  herdrAutostartScopesSessionPerWorkspace =
    lib.hasInfix "_current_workspace_herdr_session_name" herdrAutostartContent
    && lib.hasInfix "workspace-grid-state" herdrAutostartContent
    && lib.hasInfix "herdr --session" herdrAutostartContent;
in
{
  domain-terminal-bash-enabled =
    mkEvalCheck "domain-terminal-bash-enabled" cfg.programs.bash.enable
      "bash should be enabled";

  domain-terminal-carapace-enabled =
    mkEvalCheck "domain-terminal-carapace-enabled" cfg.programs.carapace.enable
      "carapace completion should be enabled";

  domain-terminal-herdr-config-is-mutable-seed =
    mkEvalCheck "domain-terminal-herdr-config-is-mutable-seed"
      (
        builtins.hasAttr ".config/herdr/config.toml.nix-source" cfg.home.file
        && !(builtins.hasAttr ".config/herdr/config.toml" cfg.home.file)
        && builtins.hasAttr "seedHerdrConfigAsMutableFile" cfg.home.activation
      )
      "herdr config.toml must be seeded as a mutable file so herdr can persist runtime UI settings: the nix-source belongs in home.file, config.toml itself must not be a read-only symlink, and the seedHerdrConfigAsMutableFile activation must run";

  domain-terminal-bash-herdr-autostart-launches-herdr =
    mkEvalCheck "domain-terminal-bash-herdr-autostart-launches-herdr"
      herdrAutostartDefinesStartAndGuardsAgainstNestingAndTmux
      "bash_herdr_autostart.sh must define _start_herdr and guard against relaunching inside HERDR_ENV or an existing TMUX session before launching herdr";

  domain-terminal-bash-herdr-autostart-scopes-session-per-workspace =
    mkEvalCheck "domain-terminal-bash-herdr-autostart-scopes-session-per-workspace"
      herdrAutostartScopesSessionPerWorkspace
      "bash_herdr_autostart.sh must attach each terminal to a per-workspace herdr session (herdr --session workspace-<N>) derived from the Hammerspoon workspace-grid-state file, so windows on different workspaces get independent, non-mirrored, reattachable sessions like tmux";

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

  domain-terminal-wezterm-ctrl-click-in-tmux =
    let
      weztermConfig = cfg.programs.wezterm.extraConfig;
      hasBypassMouseReporting = lib.hasInfix "bypass_mouse_reporting_modifiers" weztermConfig;
      hasOpenLinkAction = lib.hasInfix "OpenLinkAtMouseCursor" weztermConfig;
      hasNopDownEvent = lib.hasInfix "action = wezterm.action.Nop" weztermConfig;
      hasMouseReportingBindings = lib.hasInfix "mouse_reporting = true" weztermConfig;
    in
    mkEvalCheck "domain-terminal-wezterm-ctrl-click-in-tmux"
      (hasBypassMouseReporting && hasOpenLinkAction && hasNopDownEvent && hasMouseReportingBindings)
      "wezterm must have bypass_mouse_reporting_modifiers, OpenLinkAtMouseCursor, Nop down-event, and mouse_reporting=true bindings for ctrl+click to work inside tmux";

  domain-terminal-wezterm-webgpu-front-end-on-darwin =
    mkEvalCheck "domain-terminal-wezterm-webgpu-front-end-on-darwin"
      (lib.hasInfix "front_end = is_darwin and \"WebGpu\" or \"OpenGL\"" cfg.programs.wezterm.extraConfig)
      "wezterm must select WebGpu on darwin (to dodge the macOS OpenGL-shim teardown segfault) and OpenGL elsewhere, guarded by is_darwin";

  domain-terminal-yazi-enabled =
    mkEvalCheck "domain-terminal-yazi-enabled" cfg.programs.yazi.enable
      "yazi file manager should be enabled";
}
