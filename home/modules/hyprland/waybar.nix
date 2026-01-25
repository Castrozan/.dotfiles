{ pkgs, config, ... }:
{
  home = {
    file = {
      ".config/waybar/config".source = ../../../.config/waybar/config;
      ".config/waybar/nix.svg".source = ../../../.config/waybar/nix.svg;
      ".config/waybar/waybar-theme.css".source = ../../../.config/waybar/waybar-theme.css;
      ".config/waybar/style.css".text =
        builtins.replaceStrings [ "@HOME@" ] [ config.home.homeDirectory ]
          (builtins.readFile ../../../.config/waybar/style.css.in);
    };

    packages = with pkgs; [ waybar ];
  };
}
