{ pkgs, lib, ... }:
{
  home.file.".claude/hooks".source = import ../../home-manager/flat-hook-scripts-directory.nix {
    inherit pkgs lib;
  };
}
