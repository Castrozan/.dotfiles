# Two macbooks (different physical machines, same lucas.zanoni user).
# Activate with:
#   sudo darwin-rebuild switch --flake .#rin    (Coates)
#   sudo darwin-rebuild switch --flake .#kira   (work-Betha)
#
# rin = toosaka rin, kira = kira yoshikage. See private-config/machines.nix
# for the alias<->hostname mapping. hosts/<alias>/ owns hardware-level config,
# home/hosts/darwin/<alias>.nix owns the home-manager entry point.
{
  nix-darwin,
  home-manager,
  darwinSystem,
  darwinPkgs,
  specialArgsBase,
}:
let
  username = "lucas.zanoni";

  specialArgs = specialArgsBase // {
    inherit username;
    inherit (darwinPkgs) unstable latest;
    isNixOS = false;
    isDarwin = true;
  };

  mkHomeManagerWrapperFor =
    machineAlias:
    { inputs, ... }:
    {
      home-manager = {
        useGlobalPkgs = true;
        useUserPackages = true;
        backupFileExtension = "backup";
        overwriteBackup = true;
        sharedModules = [ inputs.stylix.homeModules.stylix ];

        extraSpecialArgs = specialArgs // {
          hostname = machineAlias;
        };
        users.${username} = import (../home/hosts/darwin + "/${machineAlias}.nix");
      };
    };

  mkDarwinHostFor = machineAlias: {
    ${machineAlias} = nix-darwin.lib.darwinSystem {
      specialArgs = specialArgs // {
        hostname = machineAlias;
      };
      system = darwinSystem;

      modules = [
        ../hosts/${machineAlias}
        home-manager.darwinModules.home-manager
        (mkHomeManagerWrapperFor machineAlias)
      ];
    };
  };

  machineAliasesWithExistingHostDirectory =
    builtins.filter (machineAlias: builtins.pathExists (../hosts + "/${machineAlias}"))
      [
        "rin"
        "kira"
      ];
in
builtins.foldl' (
  acc: machineAlias: acc // mkDarwinHostFor machineAlias
) { } machineAliasesWithExistingHostDirectory
