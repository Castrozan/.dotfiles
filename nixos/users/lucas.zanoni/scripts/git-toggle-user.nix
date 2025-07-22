{ pkgs, ... }:
let
  script = builtins.readFile ../../../../bin/git-toggle-user;
in
let
  git-toggle-user = pkgs.writeShellScriptBin "git-toggle-user" ''
    ${script}
  '';
in
{
  home.packages = [ git-toggle-user ];
}
