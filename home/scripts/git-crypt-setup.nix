{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/git-crypt-setup;
in
let
  git-crypt-setup = pkgs.writeShellScriptBin "git-crypt-setup" ''
    ${script}
  '';
in
{
  home.packages = [ git-crypt-setup ];
}
