{
  pkgs,
  config,
  lib,
  ...
}:
let
  nodejs = pkgs.nodejs_22;
  homeDir = config.home.homeDirectory;
  a2aMcpServer = import ./install.nix {
    inherit pkgs homeDir nodejs;
  };
in
{
  home.activation.installA2aMcpServer = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${pkgs.coreutils}/bin/timeout 300 ${a2aMcpServer.installScript}
  '';
}
