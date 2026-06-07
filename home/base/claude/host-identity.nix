{ hostname, ... }:
let
  machinesRegistryPath = ../../../private-config/machines.nix;
  machinesRegistry =
    if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };
  selfMachine = machinesRegistry.${hostname} or { };
  hostIdentity = {
    alias = hostname;
    platform = selfMachine.platform or "unknown";
  };
in
{
  home.file.".config/clawde/host-identity.json".text = builtins.toJSON hostIdentity;
}
