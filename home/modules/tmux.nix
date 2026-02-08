{ pkgs, ... }:
let
  settings = builtins.readFile ../../.config/tmux/settings.conf;
  binds = builtins.readFile ../../.config/tmux/binds.conf;
  catppuccinSettings = builtins.readFile ../../.config/tmux/catppuccin.conf;

  catppuccinZanoni = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "catppuccin";
    version = "zanoni.v1.0.5";
    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "catppuccin-tmux";
      rev = "zanoni.v1.0.5";
      sha256 = "0yjgkvblbqgqmz8lxk8p1jdli2g8m8sqjlp0svm0vgidx94dr77y";
    };
  };
in
{
  programs.tmux = {
    enable = true;
    baseIndex = 1;
    clock24 = false;
    shell = "${pkgs.fish}/bin/fish";
    plugins = [
      pkgs.tmuxPlugins.sensible
      pkgs.tmuxPlugins.yank
      pkgs.tmuxPlugins.resurrect
      {
        # Settings must load BEFORE plugin runs (catppuccin uses %if conditionals)
        plugin = catppuccinZanoni;
        extraConfig = catppuccinSettings;
      }
      # cpu must run AFTER catppuccin to interpolate #{cpu_percentage} in status-right
      pkgs.tmuxPlugins.cpu
    ];
    extraConfig = ''
      ${settings}
      ${binds}
    '';
  };

  home.packages = [ pkgs.xsel ];
}
