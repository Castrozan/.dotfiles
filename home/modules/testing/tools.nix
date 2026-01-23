{ pkgs, ... }:
let
  dotfiles-test = pkgs.writeShellScriptBin "dotfiles-test" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bats
        pkgs.kcov
        pkgs.bc
      ]
    }:$PATH"
    exec ~/.dotfiles/tests/run-tests.sh "$@"
  '';
  dotfiles-coverage = pkgs.writeShellScriptBin "dotfiles-coverage" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.kcov
        pkgs.bats
        pkgs.bc
      ]
    }:$PATH"
    exec ~/.dotfiles/tests/coverage.sh "$@"
  '';
in
{
  home.packages = [
    dotfiles-test
    dotfiles-coverage
    pkgs.bats
    pkgs.kcov
    pkgs.deadnix
    pkgs.statix
    pkgs.nixfmt
  ];
}
