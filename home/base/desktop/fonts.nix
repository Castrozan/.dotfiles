{ pkgs, ... }:
{
  fonts.fontconfig.enable = true;

  home.packages =
    (with pkgs; [
      nerd-fonts.fira-code
      nerd-fonts.jetbrains-mono
      fira-code
      fira-code-symbols
      noto-fonts-color-emoji
      symbola
      material-symbols
    ])
    ++ pkgs.lib.optionals pkgs.stdenv.hostPlatform.isLinux [
      pkgs.nerd-fonts.monaspace
    ];
}
