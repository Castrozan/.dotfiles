{ ... }:
let
  machinesRegistryPath = ../../../private-config/machines.nix;
in
{
  clawde = {
    machinesRegistry =
      if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

    multiplexer = "herdr";
  };
}
