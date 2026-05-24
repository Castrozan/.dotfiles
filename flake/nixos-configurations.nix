# Personal NixOS host (alias: chise / hatori chise). Activated with:
#   sudo nixos-rebuild switch --flake .?submodules=1#chise
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
  machineAlias = "chise";
  username = "zanoni";

  specialArgs = specialArgsBase // {
    inherit username;
    hostname = machineAlias;
    isNixOS = true;
    isDarwin = false;
  };
in
{
  ${machineAlias} = nixpkgs.lib.nixosSystem {
    inherit specialArgs;
    system = linuxSystem;

    modules = [
      ../hosts/${machineAlias}
      ../users/${username}/nixos.nix
      home-manager.nixosModules.home-manager
      (import ../users/${username}/nixos-home-config.nix)
    ];
  };
}
