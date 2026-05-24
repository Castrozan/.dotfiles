# Personal NixOS host (zanoni). Activated with:
#   sudo nixos-rebuild switch --flake .?submodules=1#zanoni
# Personal-only overlays, when deployed on this host, are layered in via
# a machine-local /etc/nixos/flake.nix wrapper (not in any git repo) that
# composes this flake with the personal overlay as separate inputs.
{
  nixpkgs,
  home-manager,
  linuxSystem,
  specialArgsBase,
}:
let
  username = "zanoni";

  specialArgs = specialArgsBase // {
    inherit username;
    isNixOS = true;
    isDarwin = false;
  };
in
{
  ${username} = nixpkgs.lib.nixosSystem {
    inherit specialArgs;
    system = linuxSystem;

    modules = [
      ../hosts/dellg15
      ../users/${username}/nixos.nix
      home-manager.nixosModules.home-manager
      (import ../users/${username}/nixos-home-config.nix)
    ];
  };
}
