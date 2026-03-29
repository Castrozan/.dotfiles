{ pkgs, ... }:
let
  dotfiles-test = pkgs.writeShellScriptBin "dotfiles-test" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bats
        pkgs.kcov
        pkgs.bc
        pkgs.python312Packages.pytest
        pkgs.qt6.qtdeclarative
      ]
    }:$PATH"
    export QT_DECLARATIVE_PATH="${pkgs.qt6.qtdeclarative}"
    exec ~/.dotfiles/tests/run.sh "$@"
  '';
  dotfiles-coverage = pkgs.writeShellScriptBin "dotfiles-coverage" ''
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.kcov
        pkgs.bats
        pkgs.bc
      ]
    }:$PATH"
    exec ~/.dotfiles/tests/cover/bash-coverage.sh "$@"
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
    pkgs.python312Packages.pytest
  ];
}
