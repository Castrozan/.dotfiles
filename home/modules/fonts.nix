{ pkgs, ... }:
{
  fonts.fontconfig.enable = true;

  home.packages = with pkgs; [
    nerd-fonts.fira-code
    fira-code
    fira-code-symbols
    noto-fonts-color-emoji
    symbola
  ];
}
