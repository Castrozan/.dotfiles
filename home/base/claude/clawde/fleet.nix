{ config, hostname, ... }:
let
  runtimeLocations = import ./runtime-locations.nix { homeDir = config.home.homeDirectory; };

  inherit (config.clawde) machinesRegistry;

  fleetTopology = {
    self = hostname;
    dotfilesRepo = config.clawde.dotfilesRepoPath;
    hosts = builtins.mapAttrs (_alias: machine: { inherit (machine) platform; }) machinesRegistry;
  };
in
{
  home.file.${runtimeLocations.fleetManifestRelativeToHome}.text = builtins.toJSON fleetTopology;
}
