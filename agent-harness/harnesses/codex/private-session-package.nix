{ pkgs }:
let
  sessionPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.tomlkit
    pythonPackages.websockets
  ]);

  sessionScripts = pkgs.runCommandLocal "codex-private-session-scripts" { } ''
    mkdir -p "$out"
    cp ${./scripts/session_server}/*.py "$out/"
    cp ${../../hooks/runtime/common/codex_app_server_client.py} "$out/codex_app_server_client.py"
    PYTHONPATH="$out" PYTHONDONTWRITEBYTECODE=1 ${sessionPython}/bin/python3 -c 'import launch_private_session'
  '';
in
pkgs.writeShellScript "codex-private-session" ''
  exec ${sessionPython}/bin/python3 ${sessionScripts}/launch_private_session.py "$@"
''
