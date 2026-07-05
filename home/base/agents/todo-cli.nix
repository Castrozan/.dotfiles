{ pkgs, ... }:
let
  todoCli = import ../../../agents/skills/todo/install { inherit pkgs; };
in
{
  home.packages = todoCli.packages;
}
