{
  config,
  lib,
  ...
}:
let
  openclaw = config.openclaw;
  workspaceSourcePath = ../../../agents/openclaw/workspace;

  filenames = builtins.attrNames (builtins.readDir workspaceSourcePath);

  mkWorkspaceFiles =
    destDir:
    builtins.listToAttrs (
      map (filename: {
        name = "${destDir}/${filename}";
        value.text = openclaw.substituteAgentConfig (workspaceSourcePath + "/${filename}");
      }) filenames
    );

  # Deploy to the main workspace path (~/openclaw/)
  mainWorkspace = mkWorkspaceFiles openclaw.workspacePath;

  # Deploy to the gateway's per-agent workspace (~/.openclaw/workspace-{agent}/)
  # OpenClaw resolves non-default agents to ~/.openclaw/workspace-{id}/
  gatewayWorkspace = mkWorkspaceFiles ".openclaw/workspace-${openclaw.agent}";
in
{
  home.file = mainWorkspace // gatewayWorkspace;
}
