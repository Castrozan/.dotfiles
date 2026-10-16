{
  inputs,
  release,
  system,
}:
{
  hostname,
  username,
  homeDirectory ? "/home/${username}",
  extraModules ? [ ],
}:
let
  channels = import ./channels.nix { inherit inputs system; };
in
inputs.home-manager.lib.homeManagerConfiguration {
  inherit (channels) pkgs;
  extraSpecialArgs = {
    inherit
      inputs
      hostname
      username
      homeDirectory
      ;
    inherit (channels) unstable latest;
    nixpkgs-version = release;
    home-version = release;
    isNixOS = false;
    isDarwin = false;
  };
  modules = [ ../../machine-configuration/machines/${hostname}/home.nix ] ++ extraModules;
}
