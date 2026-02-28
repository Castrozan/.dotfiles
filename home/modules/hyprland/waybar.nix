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
      ".config/waybar/scripts/workspace-window.sh" = {
        source = ../../../.config/waybar/scripts/workspace-window.sh;
        executable = true;
        force = true;
      };
      ".config/waybar/scripts/workspace-coordinator.sh" = {
        source = ../../../.config/waybar/scripts/workspace-coordinator.sh;
        executable = true;
        force = true;
      };
    };

    packages = with pkgs; [ waybar ];
  };
}
