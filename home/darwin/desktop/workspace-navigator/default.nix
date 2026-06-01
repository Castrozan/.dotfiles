{ pkgs, ... }:
let
  workspaceGrid = import ../workspace-grid.nix;
  totalWorkspaceCount = workspaceGrid.columns * workspaceGrid.rows;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "workspace-navigate" ''
      export PATH="${pkgs.aerospace}/bin:${pkgs.gawk}/bin:$PATH"
      export TOTAL_WORKSPACE_COUNT="${toString totalWorkspaceCount}"
      export WORKSPACE_GRID_COLUMNS="${toString workspaceGrid.columns}"
      exec ${pkgs.bash}/bin/bash ${./workspace-navigator.sh} "$@"
    '')
  ];
}
