{
  imports = [
    ./pkgs-darwin.nix

    ./home/git-devpro.nix
    ./home/ssh.nix
    ./home/session-vars.nix

    ../../home/core.nix

    ../../home/modules/claude/config.nix
    ../../home/modules/claude/skills.nix
    ../../home/modules/claude/hooks.nix
    ../../home/modules/claude/private.nix
    ../../home/modules/claude/workspace-trust.nix

    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/scripts.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/yazi.nix

    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/vscode/vscode.nix

    ../../home/modules/desktop/fonts.nix

    ../../home/modules/dev/git.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/scripts.nix
  ];
}
