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
    pkgs.bats
    pkgs.kcov
    dotfiles-test
    dotfiles-coverage
  ];
}
