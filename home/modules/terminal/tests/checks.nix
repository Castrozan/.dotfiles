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

  fishConfDFiles = [
    "fish/conf.d/shell-env.fish"
    "fish/conf.d/tmux.fish"
    "fish/conf.d/fish-aliases.fish"
    "fish/conf.d/fzf.fish"
    "fish/conf.d/default-directories.fish"
    "fish/conf.d/key-bindings.fish"
    "fish/conf.d/private-aliases.fish"
    "fish/conf.d/hyprland-env.fish"
    "fish/conf.d/betha-secrets.fish"
  ];

  fishFunctionFiles = [
    "fish/functions/fish_prompt.fish"
    "fish/functions/cursor.fish"
    "fish/functions/nix.fish"
  ];

  allFishConfDFilesDeployed = builtins.all (f: cfg.xdg.configFile ? "${f}") fishConfDFiles;

  allFishFunctionFilesDeployed = builtins.all (f: cfg.xdg.configFile ? "${f}") fishFunctionFiles;

  fishShellInitHasNoHardcodedSources =
    !(lib.hasInfix "source ~/.dotfiles/" cfg.programs.fish.interactiveShellInit);

  bashrcContent = builtins.readFile ../shell/.bashrc;
  bashrcHasNoHardcodedSources = !(lib.hasInfix ". $HOME/.dotfiles/" bashrcContent);

  screensaverContent = builtins.readFile ../shell/screensaver.sh;
  tmuxMainContent = builtins.readFile ../shell/tmux_main.sh;
  bashrcWithDependenciesFirst = builtins.concatStringsSep "\n" [
    screensaverContent
    tmuxMainContent
    bashrcContent
  ];
  startTmuxCallPosition = builtins.stringLength (
    builtins.head (lib.splitString "_start_tmux\n" bashrcWithDependenciesFirst)
  );
  screensaverFunctionPosition = builtins.stringLength (
    builtins.head (lib.splitString "_start_screensaver_tmux_session" screensaverContent)
  );
  tmuxFunctionsDefinedBeforeCall = startTmuxCallPosition > screensaverFunctionPosition;
in
{
  domain-terminal-fish-enabled =
    mkEvalCheck "domain-terminal-fish-enabled"
      (cfg.programs.fish.enable && builtins.length cfg.programs.fish.plugins >= 3)
      "fish should be enabled with >= 3 plugins, got ${toString (builtins.length cfg.programs.fish.plugins)}";

  domain-terminal-carapace-enabled =
    mkEvalCheck "domain-terminal-carapace-enabled" cfg.programs.carapace.enable
      "carapace completion should be enabled";

  domain-terminal-fish-conf-d-deployed =
    mkEvalCheck "domain-terminal-fish-conf-d-deployed" allFishConfDFilesDeployed
      "all fish conf.d files should be deployed via xdg.configFile";

  domain-terminal-fish-functions-deployed =
    mkEvalCheck "domain-terminal-fish-functions-deployed" allFishFunctionFilesDeployed
      "all fish function files should be deployed via xdg.configFile";

  domain-terminal-fish-no-hardcoded-sources =
    mkEvalCheck "domain-terminal-fish-no-hardcoded-sources" fishShellInitHasNoHardcodedSources
      "fish interactiveShellInit should not contain hardcoded source ~/.dotfiles/ paths";

  domain-terminal-bash-no-hardcoded-sources =
    mkEvalCheck "domain-terminal-bash-no-hardcoded-sources" bashrcHasNoHardcodedSources
      ".bashrc should not contain hardcoded . $HOME/.dotfiles/ source lines";

  domain-terminal-bash-tmux-functions-before-call =
    mkEvalCheck "domain-terminal-bash-tmux-functions-before-call" tmuxFunctionsDefinedBeforeCall
      "screensaver/tmux functions must be defined before _start_tmux call in concatenated bashrc";

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

  domain-terminal-atuin-fish = mkEvalCheck "domain-terminal-atuin-fish" (
    cfg.programs.atuin.enable && cfg.programs.atuin.enableFishIntegration
  ) "atuin should be enabled with fish integration";

  domain-terminal-yazi-enabled =
    mkEvalCheck "domain-terminal-yazi-enabled" cfg.programs.yazi.enable
      "yazi file manager should be enabled";
}
