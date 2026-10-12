{ pkgs }:
let
  scripts = ./scripts/nixos-staged-rebuild;
  metricsScripts = pkgs.runCommand "rebuild-memory-metrics-scripts" { } ''
    mkdir -p $out
    install -m 0644 ${scripts}/memory_*.py ${scripts}/staged_command.py ${scripts}/memory_components.nix $out/
  '';
in
pkgs.writeShellScript "rebuild-memory-metrics" ''
  export PATH=${
    pkgs.lib.makeBinPath [
      pkgs.coreutils
      pkgs.nix
    ]
  }:$PATH
  export REBUILD_COMMAND_TIME=${pkgs.time}/bin/time
  exec ${pkgs.python312}/bin/python3 ${metricsScripts}/memory_report.py "$@"
''
