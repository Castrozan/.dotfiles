{ pkgs, lib, ... }:
{
  fonts.fontconfig.enable = pkgs.stdenv.hostPlatform.isLinux;

  home.packages =
    (with pkgs; [
      nerd-fonts.monaspace
      nerd-fonts.fira-code
      nerd-fonts.jetbrains-mono
      fira-code
      fira-code-symbols
    ])
    ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux (
      with pkgs;
      [
        noto-fonts-color-emoji
        symbola
        material-symbols
      ]
    );
}
