# Two macbooks (different physical machines, same lucas.zanoni user).
# Activate with:
#   sudo darwin-rebuild switch --flake .#macbook-alpha   (Coates)
#   sudo darwin-rebuild switch --flake .#macbook-beta    (work-Betha)
#
# Each composes with its own users/lucas.zanoni/<alpha|beta>/home-config.nix.
# Host-level divergence (hardware, host-only services) lives under
# hosts/macbook-<alpha|beta>/.
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

  machineDirByHostname = {
    "macbook-alpha" = "alpha";
    "macbook-beta" = "beta";
  };

  mkDarwinHostFor = hostname: {
    ${hostname} = nix-darwin.lib.darwinSystem {
      specialArgs = specialArgs // {
        inherit hostname;
      };
      system = darwinSystem;

      modules = [
        ../hosts/${hostname}
        home-manager.darwinModules.home-manager
        (import ../users/${username}/${machineDirByHostname.${hostname}}/home-config.nix)
      ];
    };
  };

  hostnamesWithExistingHostDirectory =
    builtins.filter (hostname: builtins.pathExists (../hosts + "/${hostname}"))
      [
        "macbook-alpha"
        "macbook-beta"
      ];
in
builtins.foldl' (
  acc: hostname: acc // mkDarwinHostFor hostname
) { } hostnamesWithExistingHostDirectory
