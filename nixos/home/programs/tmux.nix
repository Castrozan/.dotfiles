{ pkgs, ... }:
let
  settings = builtins.readFile ../../../.config/tmux/settings.conf;
  binds = builtins.readFile ../../../.config/tmux/binds.conf;
in
{
  programs.tmux = {
    enable = true;
    clock24 = false;
    plugins = with pkgs.tmuxPlugins; [
      sensible
      yank
      catppuccin
      resurrect
    ];
    extraConfig = ''
      ${settings}
      ${binds}
    '';
  };
}
