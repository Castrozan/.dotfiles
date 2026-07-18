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
    ../scripts.nix
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
  herdrAutostartAttachesDefaultSessionNotCoupledToMacosWorkspace =
    !(lib.hasInfix "workspace-grid-state" herdrAutostartContent)
    && !(lib.hasInfix "HAMMERSPOON_WORKSPACE_STATE_FILE" herdrAutostartContent)
    && !(lib.hasInfix "herdr --session" herdrAutostartContent);

  herdrConfigContent = builtins.readFile ../../../../.config/herdr/config.toml;
  herdrConfigBindsWorkspaceChooserAsChooseSession = lib.hasInfix "goto = \"prefix+s\"" herdrConfigContent;
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

  domain-terminal-herdr-installed-from-fork-flake-input =
    mkEvalCheck "domain-terminal-herdr-installed-from-fork-flake-input"
      (builtins.any (
        pkg: (pkg.outPath or "") == inputs.herdr.packages."x86_64-linux".default.outPath
      ) cfg.home.packages)
      "herdr must be installed from the Castrozan/herdr flake input (the source-built fork carrying the session switcher), not a fetched upstream release binary";

  domain-terminal-bash-herdr-autostart-launches-herdr =
    mkEvalCheck "domain-terminal-bash-herdr-autostart-launches-herdr"
      herdrAutostartDefinesStartAndGuardsAgainstNestingAndTmux
      "bash_herdr_autostart.sh must define _start_herdr and guard against relaunching inside HERDR_ENV or an existing TMUX session before launching herdr";

  domain-terminal-bash-herdr-autostart-attaches-default-session-not-coupled-to-macos-workspace =
    mkEvalCheck
      "domain-terminal-bash-herdr-autostart-attaches-default-session-not-coupled-to-macos-workspace"
      herdrAutostartAttachesDefaultSessionNotCoupledToMacosWorkspace
      "bash_herdr_autostart.sh must launch bare herdr into the default session, never deriving a session name from the macOS workspace (no Hammerspoon workspace-grid-state read, no herdr --session): tmux-literal independence comes from separate named sessions the user creates, not from coupling session identity to the desktop the window sits on";

  domain-terminal-herdr-config-binds-workspace-chooser-as-choose-session =
    mkEvalCheck "domain-terminal-herdr-config-binds-workspace-chooser-as-choose-session"
      herdrConfigBindsWorkspaceChooserAsChooseSession
      "herdr config.toml must bind goto (prefix+s) so the workspace chooser, which lists every workspace, is tmux choose-session: with per-client active-workspace each client jumps its own view to any workspace, the reachability half of the tmux workflow";

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

  domain-terminal-wezterm-ctrl-click-opens-work-chrome-only =
    let
      weztermConfig = cfg.programs.wezterm.extraConfig;
      hasOpenUriHandler = lib.hasInfix "wezterm.on(\"open-uri\"" weztermConfig;
      routesToWorkChrome = lib.hasInfix "summon-chrome-work-profile" weztermConfig;
      hasLinuxBraveBinary = lib.hasInfix "{ \"brave\", uri }" weztermConfig;
      opensLinkAtMouseCursor = lib.hasInfix "OpenLinkAtMouseCursor" weztermConfig;
      hasPlainCtrlMods = lib.hasInfix "mods = \"CTRL\"" weztermConfig;
      noPersonalProfileRouting = !(lib.hasInfix "summon-chrome-personal-profile" weztermConfig);
      noSuperMouseBinding = !(lib.hasInfix "mods = \"CTRL|SUPER\"" weztermConfig);
    in
    mkEvalCheck "domain-terminal-wezterm-ctrl-click-opens-work-chrome-only"
      (
        hasOpenUriHandler
        && routesToWorkChrome
        && hasLinuxBraveBinary
        && opensLinkAtMouseCursor
        && hasPlainCtrlMods
        && noPersonalProfileRouting
        && noSuperMouseBinding
      )
      "wezterm ctrl+click must open the hovered link only in the work Chrome profile: an open-uri handler that unconditionally runs summon-chrome-work-profile on darwin (brave on linux), a plain CTRL mouse binding using OpenLinkAtMouseCursor, and no personal-profile routing or ctrl+super mouse binding";

  domain-terminal-wezterm-binds-reload-configuration =
    mkEvalCheck "domain-terminal-wezterm-binds-reload-configuration"
      (lib.hasInfix "action = wezterm.action.ReloadConfiguration" cfg.programs.wezterm.extraConfig)
      "wezterm must bind ReloadConfiguration to a key: across nix rebuilds the config symlink is swapped to a fresh immutable store path that wezterm's file watcher never detects, so config changes never auto-apply and the only way to load them without a full app restart is a manual reload keybinding";

  domain-terminal-wezterm-webgpu-front-end-on-darwin =
    mkEvalCheck "domain-terminal-wezterm-webgpu-front-end-on-darwin"
      (lib.hasInfix "front_end = is_darwin and \"WebGpu\" or \"OpenGL\"" cfg.programs.wezterm.extraConfig)
      "wezterm must select WebGpu on darwin (to dodge the macOS OpenGL-shim teardown segfault) and OpenGL elsewhere, guarded by is_darwin";

  domain-terminal-yazi-enabled =
    mkEvalCheck "domain-terminal-yazi-enabled" cfg.programs.yazi.enable
      "yazi file manager should be enabled";
}
