{ pkgs, ... }:
{
  imports = [ ./scripts.nix ];

  home = {
    activation.initHyprTheme = ''
      mkdir -p $HOME/.config/hypr-theme/current/theme
      mkdir -p $HOME/.config/hypr-theme/user-themes
      mkdir -p $HOME/.config/hypr-theme/backgrounds
      touch $HOME/.config/hypr-theme/current/theme/hyprland.conf
    '';

    packages = with pkgs; [ yq-go ];
  };
}
