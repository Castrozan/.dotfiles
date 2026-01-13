{ pkgs, lib, ... }:
{
  # Enable font configuration for proper glyph support
  fonts.fontconfig.enable = true;

  home.packages = with pkgs; [
    # Nerd Fonts for terminal icons and glyphs
    (nerd-fonts.fira-code)

    # Regular fonts
    fira-code
    fira-code-symbols
  ];
}