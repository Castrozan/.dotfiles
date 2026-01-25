{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/git_fzf;

  git-fzf = pkgs.writeShellScriptBin "git-fzf" ''
    ${script}
  '';
in
{
  home.packages = [ git-fzf ];
}
