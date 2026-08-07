{
  inputs,
  release,
  system,
}:
{ hostname, username }:
let
  channels = import ./channels.nix { inherit inputs system; };

  specialArgs = {
    inherit inputs hostname username;
    inherit (channels) unstable latest;
    nixpkgs-version = release;
    home-version = release;
    isNixOS = true;
    isDarwin = false;
  };

  homeManager = import ./home-manager.nix {
    inherit hostname username specialArgs;
  };
in
inputs.nixpkgs.lib.nixosSystem {
  inherit system specialArgs;

  modules = [
    ../../agent-harness/harnesses/codex/system-managed-hooks.nix
    ../../machine-configuration/machines/${hostname}/system
    inputs.home-manager.nixosModules.home-manager
    homeManager
  ];
}
