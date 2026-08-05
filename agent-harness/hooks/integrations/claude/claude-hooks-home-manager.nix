{ pkgs, lib, ... }:
{
  home.file.".claude/hooks".source = import ../../flat-hook-scripts-directory.nix {
    inherit pkgs lib;
  };
}
