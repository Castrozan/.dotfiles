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
  dotfiles-perf = pkgs.writeShellScriptBin "dotfiles-perf" ''
    set -Eeuo pipefail

    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bats
        pkgs.jq
      ]
    }:$PATH"

    _usage() {
      echo "Usage: dotfiles-perf <command> [args]"
      echo ""
      echo "Commands:"
      echo "  run [iters] [component]  Run desktop benchmarks (default: 5 iterations)"
      echo "  check                    Compare latest results against baseline"
      echo "  test                     Run perf threshold tests (bats)"
      echo "  baseline                 Measure and save new baseline"
      echo "  report                   Show benchmark history"
      echo "  all [iters]              Run benchmarks + check + threshold tests"
      echo "  shell [iters] [shell]    Run shell startup benchmark"
      echo "  rebuild [command]        Run rebuild benchmark"
      echo ""
      echo "Examples:"
      echo "  dotfiles-perf run              # benchmark all, 5 iterations"
      echo "  dotfiles-perf run 10 tmux      # benchmark tmux only, 10 iterations"
      echo "  dotfiles-perf check            # regression check against baseline"
      echo "  dotfiles-perf test             # pass/fail threshold tests"
      echo "  dotfiles-perf all              # full perf suite"
      echo "  dotfiles-perf baseline         # save new baseline"
    }

    _run() { benchmark-desktop "$@"; }

    _check() { benchmark-desktop --check-baseline; }

    _test() {
      local perf_tests
      perf_tests=$(find ~/.dotfiles/home/modules -name "perf-runtime.bats" -type f | sort)
      if [ -z "$perf_tests" ]; then
        echo "No perf-runtime.bats files found"
        exit 1
      fi
      bats $perf_tests
    }

    _baseline() { benchmark-desktop --save-baseline; }

    _report() { benchmark-desktop report; }

    _all() {
      echo "=== Performance Suite ==="
      echo ""
      echo "--- Benchmarks ---"
      benchmark-desktop "''${1:-5}"
      echo ""
      echo "--- Baseline Check ---"
      benchmark-desktop --check-baseline
      echo ""
      echo "--- Threshold Tests ---"
      _test
    }

    _shell() { benchmark-shell "$@"; }
    _rebuild() { benchmark-rebuild "$@"; }

    command="''${1:-}"
    shift || true

    case "$command" in
      run)      _run "$@" ;;
      check)    _check ;;
      test)     _test ;;
      baseline) _baseline ;;
      report)   _report ;;
      all)      _all "$@" ;;
      shell)    _shell "$@" ;;
      rebuild)  _rebuild "$@" ;;
      -h|--help|"") _usage ;;
      *)        echo "Unknown command: $command" >&2; _usage; exit 1 ;;
    esac
  '';
in
{
  home.packages = [
    dotfiles-test
    dotfiles-coverage
    dotfiles-perf
    pkgs.bats
    pkgs.kcov
    pkgs.deadnix
    pkgs.statix
    pkgs.nixfmt
    pkgs.python312Packages.pytest
  ];
}
