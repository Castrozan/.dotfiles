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
    codex-flake = {
      url = "github:castrozan/codex-flake";
      inputs.flake-utils.follows = "flake-utils";
    };
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
    let
      system = "x86_64-linux"; # linux system architecture
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      unstable = import nixpkgs-unstable {
        inherit system;
        config.allowUnfree = true;
      };
      latest = import nixpkgs-latest {
        inherit system;
        config.allowUnfree = true;
      };
      home-version = "25.05";
      specialArgs = {
        inherit
          inputs
          home-version
          pkgs
          unstable
          latest
          ;
      };
    in
    {
      # nixosConfigurations.zanoni is a NixOS system configuration that
      # can be instantiated with: nixos-rebuild switch --flake ~/.dotfiles/nixos#zanoni
      nixosConfigurations =
        let
          username = "zanoni";
        in
        {
          ${username} = nixpkgs.lib.nixosSystem {
            inherit specialArgs;
            inherit username;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix
              ./users/${username}/home.nix
              determinate.nixosModules.default
            ];
          };
        };

      # homeConfigurations.${username}@${system} is a stanalone home manager configuration
      # nix run home-manager/master -- --flake $HOME/.dotfiles/nix-home-ubuntu#lucas.zanoni@x86_64-linux switch -b backup
      homeConfigurations =
        let
          username = "lucas.zanoni";
        in
        {
          "${username}@${system}" = home-manager.lib.homeManagerConfiguration {
            inherit pkgs;

            extraSpecialArgs = specialArgs // {
              inherit username;
            };

            modules = [ ./users/${username}/home.nix ];
          };
        };
    };
}
