{
  description = "not A very basic flake";

  inputs = {
    # For stable packages
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.05";
    # For packages not yet in nixpkgs
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    # For latest bleeding edge packages - daily* updated
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    home-manager.url = "github:nix-community/home-manager/release-25.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    determinate.url = "https://flakehub.com/f/DeterminateSystems/determinate/*";

    catppuccin-bat.url = "github:catppuccin/bat";
    catppuccin-bat.flake = false;
    codex-flake.url = "github:castrozan/codex-flake";
    codex-flake.inputs.flake-utils.follows = "flake-utils";
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
      specialArgsBase = {
        inherit
          home-version
          inputs
          unstable
          latest
          ;
      };
    in
    {
      # nixosConfigurations.${username} is a NixOS system configuration
      # nixos-rebuild switch --flake ~/.dotfiles/nixos#${username}
      nixosConfigurations =
        let
          username = "zanoni";
          specialArgs = specialArgsBase // {
            inherit username;
          };
        in
        {
          "${username}" = nixpkgs.lib.nixosSystem {
            inherit specialArgs;
            inherit system;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix
              home-manager.nixosModules.home-manager
              (import ./users/${username}/nixos-home-config.nix)
              determinate.nixosModules.default
            ];
          };
        };

      # homeConfigurations.${username}@${system} is a standalone home manager configuration
      # nix run home-manager/master -- --flake $HOME/.dotfiles/nixos#${username}@${system} switch -b backup
      homeConfigurations =
        let
          username = "lucas.zanoni";
          specialArgs = specialArgsBase // {
            inherit username;
          };
        in
        {
          "${username}@${system}" = home-manager.lib.homeManagerConfiguration {
            inherit pkgs;

            extraSpecialArgs = specialArgs;

            modules = [ ./users/${username}/home.nix ];
          };
        };
    };
}
