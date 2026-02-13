{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  directories = [
    "memory"
    "projects"
  ];

  seedFiles = [
    "HEARTBEAT.md"
    "TOOLS.md"
  ];

  mkDirsScript = lib.concatStringsSep "\n" (
    lib.concatMap (
      agentName:
      let
        agent = openclaw.agents.${agentName};
        base = "${homeDir}/${agent.workspace}";
      in
      map (dir: "mkdir -p \"${base}/${dir}\"") directories
    ) (lib.attrNames openclaw.enabledAgents)
  );

  mkSeedFilesScript = lib.concatStringsSep "\n" (
    lib.concatMap (
      agentName:
      let
        agent = openclaw.agents.${agentName};
        base = "${homeDir}/${agent.workspace}";
      in
      map (filename: ''
        [ -f "${base}/${filename}" ] || touch "${base}/${filename}"
      '') seedFiles
    ) (lib.attrNames openclaw.enabledAgents)
  );

  fixSessionPathsScript = pkgs.writeShellScript "openclaw-fix-session-paths" ''
    set -euo pipefail
    for sessionsJson in "${homeDir}"/.openclaw/agents/*/sessions/sessions.json; do
      [ -f "$sessionsJson" ] || continue
      if ${pkgs.gnugrep}/bin/grep -q '"sessionFile"' "$sessionsJson" 2>/dev/null; then
        ${pkgs.jq}/bin/jq 'walk(if type == "object" and .sessionFile then .sessionFile |= split("/")[-1] else . end)' \
          "$sessionsJson" | ${pkgs.moreutils}/bin/sponge "$sessionsJson"
      fi
    done
  '';
in
{
  home.activation.openclawDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${mkDirsScript}
    ${mkSeedFilesScript}
    run ${fixSessionPathsScript}
  '';
}
