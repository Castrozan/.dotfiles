{ pkgs }:
pkgs.writeShellScriptBin "avatar-switch-latency" ''
  export PYTHONPATH=${../scripts/listening}
  exec ${pkgs.python312}/bin/python3 ${../scripts/doctor}/switch_latency.py "$@"
''
