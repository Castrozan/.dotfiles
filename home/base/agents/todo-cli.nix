{ pkgs, ... }:
let
  todoCli = import ../../../agent-harness/agent-instructions/skills/todo/install { inherit pkgs; };
in
{
  home.packages = todoCli.packages;
}
