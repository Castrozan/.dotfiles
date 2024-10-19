{ pkgs, config, ... }: 
let
  kittyConf = builtins.readFile ../../../.config/kitty/kitty.conf;
in
{
  programs.kitty = {
    enable = true;
    theme = "Catppuccin-Mocha";
    font = {
      name = "Fira Code";
      size = 18;
      package = pkgs.fira-code;
    };
    extraConfig = kittyConf;
  };

  home.file.".config/kitty/startup.conf".source = ../../../.config/kitty/startup.conf;
}