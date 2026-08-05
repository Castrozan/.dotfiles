{ pkgs, ... }:
let
  rilCli = import ../../../agent-harness/agent-instructions/skills/ril/install { inherit pkgs; };
in
{
  home.packages = rilCli.packages;
}
