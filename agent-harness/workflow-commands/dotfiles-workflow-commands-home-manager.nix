{
  pkgs,
  lib,
  config,
  ...
}:
let
  workflowCommandDirectory = ./.;

  unwrappedClaudeRuntimePath = lib.makeBinPath [
    config.claude.unwrappedPackage
    pkgs.git
  ];

  mkWorkflowCommand =
    workflowName:
    pkgs.writeShellScriptBin workflowName ''
      export PATH="${unwrappedClaudeRuntimePath}:$PATH"
      export DOTFILES_WORKFLOW_NAME="${workflowName}"
      exec ${pkgs.python312}/bin/python3 ${workflowCommandDirectory}/run_dotfiles_workflow.py "$@"
    '';
in
{
  imports = [ ../harnesses/claude-code/binary.nix ];

  home.packages = map mkWorkflowCommand [
    "dotfiles-change-review"
    "dotfiles-housekeeping"
  ];
}
