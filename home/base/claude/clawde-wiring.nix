{ config, ... }:
let
  machinesRegistryPath = ../../../private-config/machines.nix;
in
{
  clawde = {
    machinesRegistry =
      if builtins.pathExists machinesRegistryPath then import machinesRegistryPath else { };

    claudePackage = config.claude.package;

    multiplexer = "herdr";
  };
}
