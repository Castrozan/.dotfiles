{
  pkgs,
  lib,
  hostname,
  ...
}:
let
  # kcov drives bash coverage but is Linux-only in nixpkgs. Omit it from the
  # darwin closures so home-manager can still build dotfiles-test there; the
  # coverage helper is omitted entirely.
  kcovPackages = lib.optional pkgs.stdenv.hostPlatform.isLinux pkgs.kcov;

  testSuiteEnvironment = import ./test-suite-environment.nix { inherit pkgs; };

  mkTestingPythonScript = import ./make-testing-python-script.nix {
    inherit pkgs hostname;
  };

  dotfiles-test = pkgs.writeShellScriptBin "dotfiles-test" ''
    export PATH="${
      pkgs.lib.makeBinPath (
        [
          pkgs.bats
          pkgs.bc
          testSuiteEnvironment
          pkgs.qt6.qtdeclarative
        ]
        ++ kcovPackages
      )
    }:$PATH"
    export QT_DECLARATIVE_PATH="${pkgs.qt6.qtdeclarative}"
    exec ~/.dotfiles/repository/verification/run.sh "$@"
  '';
  dotfiles-coverage = pkgs.writeShellScriptBin "dotfiles-coverage" ''
    export PATH="${
      pkgs.lib.makeBinPath (
        [
          pkgs.bats
          pkgs.bc
        ]
        ++ kcovPackages
      )
    }:$PATH"
    exec ~/.dotfiles/repository/verification/cover/bash-coverage.sh "$@"
  '';
  dotfiles-perf = mkTestingPythonScript {
    name = "dotfiles-perf";
    source = ./scripts/dotfiles_perf.py;
    runtimeInputs = [ pkgs.bats ];
  };
in
{
  home.packages = [
    dotfiles-test
    dotfiles-coverage
    dotfiles-perf
    pkgs.bats
    pkgs.deadnix
    pkgs.statix
    pkgs.nixfmt
  ]
  ++ kcovPackages;
}
