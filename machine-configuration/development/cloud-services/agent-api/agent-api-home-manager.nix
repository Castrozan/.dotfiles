{ pkgs, hostname, ... }:
let
  inherit (pkgs) lib;
  machineRegistryPath = ../../../../private-configuration/machines.nix;
  machineRegistry = lib.optionalAttrs (builtins.pathExists machineRegistryPath) (
    import machineRegistryPath
  );

  optionalField =
    entry: registryName: inventoryName:
    lib.optionalAttrs (entry ? ${registryName}) { ${inventoryName} = entry.${registryName}; };

  inventoryHost =
    name: entry:
    {
      inherit name;
      ssh_alias = entry.sshAlias or name;
      trust = entry.trust or "owned";
    }
    // optionalField entry "system" "system"
    // optionalField entry "cores" "cores"
    // optionalField entry "memoryGigabytes" "memory_gigabytes";

  computeInventoryFile =
    if machineRegistry == { } then
      null
    else
      pkgs.writeText "agent-api-compute-inventory.json" (
        builtins.toJSON {
          self = hostname;
          hosts = lib.mapAttrsToList inventoryHost machineRegistry;
        }
      );
in
{
  home.packages = [
    (import ./package.nix { inherit pkgs computeInventoryFile; })
    (import ./job-package.nix { inherit pkgs; })
  ];
}
