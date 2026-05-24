# Two macbooks (different machines, same lucas.zanoni user). Activate with:
#   sudo darwin-rebuild switch --flake .#macbook-alpha
#   sudo darwin-rebuild switch --flake .#macbook-beta   (when added)
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
    unstable = darwinPkgs.unstable;
    latest = darwinPkgs.latest;
    isNixOS = false;
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
        (import ../users/${username}/darwin-home-config.nix)
      ];
    };
  };
in
mkDarwinHostFor "macbook-alpha"
