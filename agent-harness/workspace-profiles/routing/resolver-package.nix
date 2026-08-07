{ pkgs, routingTableFile }:
pkgs.writeShellScriptBin "resolve-workspace-profile" ''
  export PATH="${pkgs.git}/bin:$PATH"
  export PYTHONPATH="${./.}"
  export AGENT_WORKSPACE_PROFILE_ROUTING_TABLE="''${AGENT_WORKSPACE_PROFILE_ROUTING_TABLE:-${routingTableFile}}"
  exec ${pkgs.python312}/bin/python3 ${./resolve-workspace-profile} "$@"
''
