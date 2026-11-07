{
  pkgs,
  lib,
  config,
  ...
}:
let
  workflowCommandDirectory = ./.;

  unwrappedClaudeRuntimePath = lib.makeBinPath (
    lib.optional (config ? claude) config.claude.unwrappedPackage ++ [ pkgs.git ]
  );

  mkWorkflowCommand =
    {
      commandName,
      workflowName ? "",
      workflowScriptPath ? "",
      argumentNames,
    }:
    pkgs.writeShellScriptBin commandName ''
      export PATH="${unwrappedClaudeRuntimePath}:$PATH"
      export DOTFILES_WORKFLOW_COMMAND="${commandName}"
      export DOTFILES_WORKFLOW_NAME="${workflowName}"
      export DOTFILES_WORKFLOW_SCRIPT_PATH="${workflowScriptPath}"
      export DOTFILES_WORKFLOW_ARGUMENTS="${lib.concatStringsSep " " argumentNames}"
      exec ${pkgs.python312}/bin/python3 ${workflowCommandDirectory}/run_dotfiles_workflow.py "$@"
    '';

  workflowWaitCommand = pkgs.writeShellScriptBin "dotfiles-workflow-wait" ''
    exec ${pkgs.python312}/bin/python3 ${workflowCommandDirectory}/wait_for_dotfiles_workflow.py "$@"
  '';
in
{
  home.packages = [
    workflowWaitCommand
  ]
  ++ map mkWorkflowCommand [
    {
      commandName = "dotfiles-housekeeping";
      workflowName = "dotfiles-housekeeping";
      argumentNames = [
        "root"
        "subtree"
      ];
    }
    {
      commandName = "dotfiles-compose-page";
      workflowName = "compose-page";
      argumentNames = [
        "brief"
        "output"
        "constraints"
      ];
    }
    {
      commandName = "dotfiles-research-pulse";
      workflowScriptPath = "${config.agentPlugins.bundle}/plugin/skills/research/research-pulse.workflow.js";
      argumentNames = [ "topic" ];
    }
  ];
}
