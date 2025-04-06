{
  description = "not A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-24.11";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager/release-24.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    catppuccin-bat = {
      url = "github:catppuccin/bat";
      flake = false;
    };

    flake-utils.url = "github:numtide/flake-utils";

    claude-desktop = {
      url = "github:k3d3/claude-desktop-linux-flake";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-unstable,
      home-manager,
      claude-desktop,
      ...
    }:
    {
      # nixosConfigurations.zanoni is a NixOS system configuration that
      # can be instantiated with: nixos-rebuild switch --flake .#zanoni
      nixosConfigurations = {
        zanoni =
          let
            username = "zanoni";
            system = "x86_64-linux";
            unstable = import nixpkgs-unstable {
              inherit system;
              config.allowUnfree = true;
            };
            specialArgs = {
              inherit username inputs unstable;
            };
          in
          nixpkgs.lib.nixosSystem {
            inherit specialArgs;
            inherit system;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix

              home-manager.nixosModules.home-manager
              {
                home-manager.useGlobalPkgs = true;
                home-manager.useUserPackages = true;

                home-manager.extraSpecialArgs = specialArgs;
                home-manager.users.${username} = import ./users/${username}/home.nix;
              }
            ];
          };
      };
    };
}
