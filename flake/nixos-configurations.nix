# Personal NixOS host (zanoni). Activated with:
#   sudo nixos-rebuild switch --flake .?submodules=1#zanoni
# openclaw-zan, when deployed on this host, layers in via a
# machine-local /etc/nixos/flake.nix wrapper (not in any git repo) that
# takes both .dotfiles and openclaw-zan as flake inputs and composes
# them. This flake itself never references openclaw.
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
