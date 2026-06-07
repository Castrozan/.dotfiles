{ config, hostname, ... }:
let
  runtimeLocations = import ./runtime-locations.nix { homeDir = config.home.homeDirectory; };

  machinesRegistryPath = ../../../../private-config/machines.nix;
  machinesRegistry =
    if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };
  selfMachine = machinesRegistry.${hostname} or { };
  hostIdentity = {
    alias = hostname;
    platform = selfMachine.platform or "unknown";
  };
in
{
  home.file.${runtimeLocations.hostIdentityRelativeToHome}.text = builtins.toJSON hostIdentity;
}
