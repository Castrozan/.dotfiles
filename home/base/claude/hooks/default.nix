{ pkgs, lib, ... }:
{
  home.file.".claude/hooks".source = import ../../agent-hooks/flat-hook-scripts-directory.nix {
    inherit pkgs lib;
  };
}
