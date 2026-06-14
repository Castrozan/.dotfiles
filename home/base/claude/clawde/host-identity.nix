{ config, hostname, ... }:
let
  runtimeLocations = import ./runtime-locations.nix { homeDir = config.home.homeDirectory; };

  inherit (config.clawde) machinesRegistry;
  selfMachine = machinesRegistry.${hostname} or { };
  hostIdentity = {
    alias = hostname;
    platform = selfMachine.platform or "unknown";
  };
in
{
  home.file.${runtimeLocations.hostIdentityRelativeToHome}.text = builtins.toJSON hostIdentity;
}
