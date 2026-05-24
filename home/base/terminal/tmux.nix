{ pkgs, lib, ... }:
let
  settings = builtins.readFile ../../../.config/tmux/settings.conf;
  binds = builtins.readFile ../../../.config/tmux/binds.conf;
  catppuccinSettings = builtins.readFile ../../../.config/tmux/catppuccin.conf;

  catppuccinZanoni = pkgs.tmuxPlugins.mkTmuxPlugin {
    pluginName = "catppuccin";
    version = "zanoni.v1.0.6";
    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "catppuccin-tmux";
      rev = "zanoni.v1.0.6";
      sha256 = "1w49sjcvzblga8cc8pf9cxnksnc9gs9kfdh7nqdg3p39x8mi4xv9";
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
        plugin = catppuccinZanoni;
        extraConfig = catppuccinSettings;
      }
      pkgs.tmuxPlugins.cpu
    ];
    extraConfig = ''
      set-environment -g PATH "${pkgs.tmux}/bin:${pkgs.coreutils}/bin:${pkgs.bash}/bin:/etc/profiles/per-user/''$USER/bin:''$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/run/current-system/sw/bin:/usr/sbin:/usr/bin:/bin"
      ${settings}
      ${binds}
    '';
  };

  home.packages = lib.optionals pkgs.stdenv.isLinux [ pkgs.xsel ];
}
