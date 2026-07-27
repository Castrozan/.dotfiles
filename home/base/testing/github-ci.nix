{ pkgs, ... }:
let
  dotfiles-ci = pkgs.writeShellScriptBin "dotfiles-ci" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.gh
        pkgs.git
      ]
    }:$PATH"
    exec ${pkgs.python3}/bin/python3 ~/.dotfiles/home/base/testing/scripts/dotfiles_ci.py "$@"
  '';
in
{
  home.packages = [ dotfiles-ci ];
}
