{ config, pkgs, lib, inputs, username, ... }:

{
  ##################################################################################################################
  #
  # All Zanoni's Home Manager Configuration
  #
  ##################################################################################################################

  imports = [
    ../../home/core.nix

    # ../../home/fcitx5
    # ../../home/i3
    ../../home/kitty
    #../../home/wallpaper
    ../../home/programs
    ../../home/gnome
    # ../../home/rofi
    # ../../home/shell
  ];
}
