# Two macbooks (different physical machines, same lucas.zanoni user).
# Activate with:
#   sudo darwin-rebuild switch --flake .#rin    (Coates)
#   sudo darwin-rebuild switch --flake .#kira   (work-Betha)
#
# rin = toosaka rin, kira = kira yoshikage. See private-config/machines.nix
# for the alias↔hostname mapping. hosts/<alias>/ owns hardware-level config,
# users/lucas.zanoni/<alias>/home-config.nix owns home-manager wiring.
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

  mkDarwinHostFor = machineAlias: {
    ${machineAlias} = nix-darwin.lib.darwinSystem {
      specialArgs = specialArgs // {
        hostname = machineAlias;
      };
      system = darwinSystem;

      modules = [
        ../hosts/${machineAlias}
        home-manager.darwinModules.home-manager
        (import ../users/${username}/${machineAlias}/home-config.nix)
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
