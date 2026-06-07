{ config, hostname, ... }:
let
  runtimeLocations = import ./runtime-locations.nix { homeDir = config.home.homeDirectory; };

  machinesRegistryPath = ../../../../private-config/machines.nix;
  machinesRegistry =
    if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

  fleetTopology = {
    self = hostname;
    dotfilesRepo = "${config.home.homeDirectory}/.dotfiles";
    hosts = builtins.mapAttrs (_alias: machine: { inherit (machine) platform; }) machinesRegistry;
  };
in
{
  home.file.${runtimeLocations.fleetManifestRelativeToHome}.text = builtins.toJSON fleetTopology;
}
