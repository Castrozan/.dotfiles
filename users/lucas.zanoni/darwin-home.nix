{ lib, inputs, ... }:
let
  macbookAlphaPrivateConfigDirectory = ../../private-config/machines/macbook-alpha;
  macbookAlphaPrivateConfigExists = builtins.pathExists macbookAlphaPrivateConfigDirectory;
in
{
  imports = [
    ./pkgs.nix

    ./home/git.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/clawde-silver.nix

    ../../home/core.nix

    ../../home/modules/agents

    ../../home/modules/claude
    ../../home/modules/codex

    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/scripts.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/yazi

    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/vscode/vscode.nix

    ../../home/modules/desktop/theming
    ../../home/modules/desktop/aerospace.nix
    ../../home/modules/desktop/application-launcher
    ../../home/modules/desktop/brave
    ../../home/modules/desktop/workspace-navigator
    ../../home/modules/desktop/workspace-switcher-client
    ../../home/modules/desktop/fonts.nix
    ../../home/modules/desktop/karabiner
    ../../home/modules/desktop/keyboard-layout
    ../../home/modules/desktop/maccy.nix
    ../../home/modules/desktop/spaceman.nix
    ../../home/modules/desktop/summon-browser
    ../../home/modules/desktop/home-assistant-remote.nix

    ../../home/modules/dev/devenv.nix
    ../../home/modules/dev/git.nix
    ../../home/modules/dev/glab.nix
    ../../home/modules/dev/jira.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/scripts.nix

    ../../home/modules/terminal/bad-apple.nix
    ../../home/modules/terminal/cbonsai.nix
    ../../home/modules/terminal/cmatrix.nix

    ../../home/modules/security/agenix.nix

    ../../home/modules/network/tailscale-daemon.nix

    ../../home/modules/media/obsidian
    ../../home/modules/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ]
  ++ lib.optionals macbookAlphaPrivateConfigExists [
    "${macbookAlphaPrivateConfigDirectory}/clawde-pm.nix"
  ];
}
