{ pkgs, config, ... }:
{
  home = {
    file = {
      ".config/waybar/config" = {
        source = ../../../.config/waybar/config;
        force = true;
      };
      ".config/waybar/nix.svg" = {
        source = ../../../.config/waybar/nix.svg;
        force = true;
      };
      ".config/waybar/waybar-theme.css" = {
        source = ../../../.config/waybar/waybar-theme.css;
        force = true;
      };
      ".config/waybar/style.css" = {
        text = builtins.replaceStrings [ "@HOME@" ] [ config.home.homeDirectory ] (
          builtins.readFile ../../../.config/waybar/style.css.in
        );
        force = true;
      };
    };

    packages = with pkgs; [ waybar ];
  };
}
