{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/dotfiles-quick-commit;

  dotfiles-quick-commit = pkgs.writeShellScriptBin "dotfiles-quick-commit" ''
    ${script}
  '';
in
{
  home.packages = [ dotfiles-quick-commit ];
}
