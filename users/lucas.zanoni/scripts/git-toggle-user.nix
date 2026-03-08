{ pkgs, ... }:
let
  git-toggle-user = pkgs.writeShellScriptBin "git-toggle-user" (
    builtins.readFile ../../../home/modules/dev/scripts/git-toggle-user
  );
in
{
  home.packages = [ git-toggle-user ];
}
