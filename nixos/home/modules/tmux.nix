{ pkgs, ... }:
let
  settings = builtins.readFile ../../../.config/tmux/settings.conf;
  binds = builtins.readFile ../../../.config/tmux/binds.conf;
  catppuccinSettings = builtins.readFile ../../../.config/tmux/catppuccin.conf;

  catppuccinZanoni = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "catppuccin";
    version = "zanoni.v1.0.3";
    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "tmux";
      rev = "zanoni.v1.0.3";
      sha256 = "0aYa1LY8BRGkU3Cd1l7dmLnGsFXbbRjmCtInYfiEwTA=";
    };
  };
in
{
  programs.tmux = {
    enable = true;
    clock24 = false;
    shell = "${pkgs.fish}/bin/fish";
    plugins = [
      pkgs.tmuxPlugins.sensible
      pkgs.tmuxPlugins.yank
      pkgs.tmuxPlugins.resurrect
      pkgs.tmuxPlugins.cpu
      {
        plugin = catppuccinZanoni;
        extraConfig = ''
          ${catppuccinSettings}
        '';
      }
    ];
    extraConfig = ''
      ${settings}
      ${binds}
    '';
  };
}
