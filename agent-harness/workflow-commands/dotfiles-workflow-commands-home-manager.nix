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
    workflowName:
    pkgs.writeShellScriptBin workflowName ''
      export PATH="${unwrappedClaudeRuntimePath}:$PATH"
      export DOTFILES_WORKFLOW_NAME="${workflowName}"
      exec ${pkgs.python312}/bin/python3 ${workflowCommandDirectory}/run_dotfiles_workflow.py "$@"
    '';
in
{
  home.packages = map mkWorkflowCommand [
    "dotfiles-housekeeping"
  ];
}
