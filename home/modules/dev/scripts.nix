{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "git-fzf" (builtins.readFile ./scripts/git-fzf))
  ];
}
