{
  pkgs,
  herdrClientPackage,
  a2aClientPackage,
}:
let
  migrationScripts = pkgs.runCommandLocal "agent-session-codex-launcher-migration-scripts" { } ''
    mkdir -p "$out/agent_session"
    cp ${./agent-session-codex-launcher-migration.py} "$out/agent-session-codex-launcher-migration.py"
    cp ${./agent_session}/codex_*.py "$out/agent_session/"
    ${pkgs.python312}/bin/python3 -E -s -B "$out/agent-session-codex-launcher-migration.py" --help >/dev/null
  '';
in
pkgs.writeShellApplication {
  name = "agent-session-codex-launcher-migration";
  runtimeInputs = [
    herdrClientPackage
    a2aClientPackage
  ];
  text = ''
    exec ${pkgs.python312}/bin/python3 -E -s -B ${migrationScripts}/agent-session-codex-launcher-migration.py "$@"
  '';
}
