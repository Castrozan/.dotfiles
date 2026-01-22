{ pkgs, ... }:
let
  script = builtins.readFile ../../../bin/git-toggle-user;

  git-toggle-user = pkgs.writeShellScriptBin "git-toggle-user" ''
    ${script}
  '';
in
{
  home.packages = [ git-toggle-user ];
}
