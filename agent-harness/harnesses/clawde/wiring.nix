_:
let
  machinesRegistryPath = ../../../private-configuration/machines.nix;
in
{
  clawde = {
    machinesRegistry =
      if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

    multiplexer = "herdr";
  };
}
