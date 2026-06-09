{
  pkgs,
  lib,
  ...
}:
let
  projectManagerRuntimeInstructions = builtins.readFile ./instructions/pm-runtime.md;

  seedProjectManagerWorkspaceScript = pkgs.writeShellScript "seed-one-workspace-project-manager" (
    builtins.readFile ./scripts/seed-pm-workspace.sh
  );

  buildProjectManagerPersonality = projectName: ''
    <identity>
    You are the project manager for ${projectName}. You own direction, priorities, state, and enforcement for this workspace. Lead the project end-to-end - read its CLAUDE.md, README.md, and .pm/HEARTBEAT.md to ground yourself, then drive priorities, decisions, and execution.
    </identity>
  '';
in
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options.typeParams.project-manager = lib.mkOption {
          type = lib.types.submodule {
            options = {
              projectName = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Name of the project this PM owns. Drives the default personality template.";
              };
              projectDirectory = lib.mkOption {
                type = lib.types.nullOr lib.types.str;
                default = null;
                description = "Absolute path to the project the PM owns. Becomes the agent workspace; state lives at <projectDirectory>/.pm/HEARTBEAT.md. Null falls back to the clawde default workspace.";
              };
            };
          };
          default = { };
          description = "Parameters for agents of type 'project-manager'.";
        };
      }
    );
  };

  config.clawde.agentTypes.project-manager = {
    runtimeInstructions = projectManagerRuntimeInstructions;
    personalityTemplateFor =
      agent:
      let
        inherit (agent.typeParams.project-manager) projectName;
      in
      if projectName == null then null else buildProjectManagerPersonality projectName;
    workspaceDirectoryFor = agent: agent.typeParams.project-manager.projectDirectory;
    agentActivationScriptFor =
      { workspaceDirectory, ... }:
      "${seedProjectManagerWorkspaceScript} ${lib.escapeShellArg workspaceDirectory}";
    defaultModel = "claude-opus-4-8";
    defaultPermissionMode = "bypassPermissions";
    defaultActiveHoursStart = 8;
    defaultActiveHoursEnd = 20;
    requiredParams = [ "projectName" ];
  };
}
