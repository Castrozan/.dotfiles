{ lib, config, pkgs, ... }:
let
  ws = "${config.home.homeDirectory}/${config.openclaw.workspace}";
  bootstrapScript = pkgs.writeShellScript "bootstrap-workspace"
    (builtins.readFile ../../../agents/scripts/bootstrap-workspace.sh);
in
{
  home.activation.openclawWritableFiles = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${bootstrapScript} "${ws}"
  '';
}
