{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  agentSessionControlScripts = ../../../agents/scripts;
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
  runtimePath = lib.makeBinPath (
    [ herdrPackage ] ++ lib.optionals pkgs.stdenv.isLinux [ pkgs.procps ]
  );
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "agent-session" ''
      export PATH="${runtimePath}:$PATH"
      exec ${pkgs.python312}/bin/python3 ${agentSessionControlScripts}/agent_session_control.py "$@"
    '')
  ];
}
