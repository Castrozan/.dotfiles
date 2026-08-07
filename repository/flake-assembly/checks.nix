{
  inputs,
  self,
  release,
  systems,
}:
builtins.listToAttrs (
  map (
    system:
    let
      channels = import ./channels.nix { inherit inputs system; };
    in
    {
      name = system;
      value = import ../verification/nix-checks {
        inherit inputs self;
        inherit (channels) pkgs;
        inherit (inputs.nixpkgs) lib;
        nixpkgs-version = release;
        home-version = release;
      };
    }
  ) systems
)
