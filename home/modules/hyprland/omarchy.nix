{ pkgs, ... }:
{
  imports = [ ./omarchy-scripts.nix ];

  home = {
    file = {
      ".config/omarchy/themes".source = ../../../.config/omarchy/themes;
      ".config/omarchy/themed".source = ../../../.config/omarchy/themed;
    };

    activation.initOmarchyTheme = ''
      mkdir -p $HOME/.config/omarchy/current/theme
      mkdir -p $HOME/.config/omarchy/user-themes
      mkdir -p $HOME/.config/omarchy/backgrounds
      touch $HOME/.config/omarchy/current/theme/hyprland.conf
    '';

    packages = with pkgs; [ yq-go ];
  };
}
