{ pkgs }:
pkgs.writeShellScriptBin "agent-api-job" ''
  export PYTHONDONTWRITEBYTECODE=1
  exec ${pkgs.python312}/bin/python3 ${./scripts}/agent_api_job_cli.py "$@"
''
