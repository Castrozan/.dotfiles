{
  lib,
  hostname,
  ...
}:
let
  privateConfigRoot = ../../../../private-config;
  privateClawdePmPath = "${toString privateConfigRoot}/machines/${hostname}/clawde-pm.nix";
  privateClawdePmExists = builtins.pathExists privateClawdePmPath;
in
{
  imports = lib.optionals privateClawdePmExists [
    privateClawdePmPath
  ];
}
