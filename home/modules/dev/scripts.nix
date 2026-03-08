{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "git-fzf" (builtins.readFile ./scripts/git-fzf))
    (pkgs.writeShellScriptBin "dotfiles-quick-commit" (
      builtins.readFile ./scripts/dotfiles-quick-commit
    ))
  ];
}
