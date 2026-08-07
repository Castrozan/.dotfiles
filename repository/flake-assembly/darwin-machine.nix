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
    isNixOS = false;
    isDarwin = true;
  };

  homeManager = import ./home-manager.nix {
    inherit hostname username specialArgs;
    sharedModules = [ inputs.stylix.homeModules.stylix ];
  };
in
inputs.nix-darwin.lib.darwinSystem {
  inherit system specialArgs;

  modules = [
    ../../agent-harness/harnesses/codex/system-managed-hooks.nix
    ../../machine-configuration/machines/${hostname}/system
    inputs.home-manager.darwinModules.home-manager
    homeManager
  ];
}
