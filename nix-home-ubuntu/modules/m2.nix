{ pkgs, ... }:
{
  # create a symlink to the m2 directory
  home.file.".m3".source = ../dotfiles/.m2;
}
