{ pkgs, ... }:
let
  conf = builtins.readFile ../../../.config/tmux/tmux.conf;
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
      ${conf}
    '';
  };
}
