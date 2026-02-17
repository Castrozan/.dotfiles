{
  lib,
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

  removeGatewayBackupFiles = lib.concatStringsSep "\n" (
    map (
      agentName:
      let
        agent = openclaw.agents.${agentName};
        base = "${homeDir}/${agent.workspace}";
      in
      ''
        find "${base}" -maxdepth 1 -name "*.backup-*" -type f -delete 2>/dev/null || true
      ''
    ) (lib.attrNames openclaw.enabledAgents)
  );

in
{
  home.activation.openclawDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${mkDirsScript}
    ${mkSeedFilesScript}
    ${removeGatewayBackupFiles}
  '';
}
