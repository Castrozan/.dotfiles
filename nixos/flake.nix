{
  description = "not A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    home-manager.url = "github:nix-community/home-manager/release-25.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/*";

    catppuccin-bat = {
      url = "github:catppuccin/bat";
      flake = false;
    };
    #claude-desktop = {
    #  url = "github:k3d3/claude-desktop-linux-flake";
    #  inputs.nixpkgs.follows = "nixpkgs";
    #  inputs.flake-utils.follows = "flake-utils";
    #};
    codex-flake = {
      url = "github:castrozan/codex-flake";
      inputs.flake-utils.follows = "flake-utils";
    };
    #zen-browser = {
    #  url = "github:MarceColl/zen-browser-flake";
    #  inputs.nixpkgs.follows = "nixpkgs";
    #};
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-unstable,
      nixpkgs-latest,
      home-manager,
      determinate,
      ...
    }:
    {
      # nixosConfigurations.zanoni is a NixOS system configuration that
      # can be instantiated with: nixos-rebuild switch --flake ~/.dotfiles/nixos#zanoni
      nixosConfigurations = {
        zanoni =
          let
            username = "zanoni";
            system = "x86_64-linux";
            unstable = import nixpkgs-unstable {
              inherit system;
              config.allowUnfree = true;
            };
            latest = import nixpkgs-latest {
              inherit system;
              config.allowUnfree = true;
            };
            specialArgs = {
              inherit
                username
                inputs
                unstable
                latest
                ;
            };
          in
          nixpkgs.lib.nixosSystem {
            inherit specialArgs;
            inherit system;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix
              determinate.nixosModules.default

              home-manager.nixosModules.home-manager
              {
                home-manager.useGlobalPkgs = true;
                home-manager.useUserPackages = true;
                home-manager.backupFileExtension = "backup";

                home-manager.extraSpecialArgs = specialArgs;
                home-manager.users.${username} = import ./users/${username}/home.nix;
              }
            ];
          };
      };
    };
}
