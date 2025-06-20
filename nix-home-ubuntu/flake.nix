{
  description = "Nix e Home Manager configuration for my Ubuntu company laptop";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-latest,
      home-manager,
      ...
    }:
    let
      system = "x86_64-linux";
      username = "lucas.zanoni";
      home-version = "23.11";
      latest = import nixpkgs-latest {
        inherit system;
        config.allowUnfree = true;
      };
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;
      };
      specialArgs = {
        inherit inputs;
      };
    in
    {
      homeConfigurations = {
        "${username}@${system}" = home-manager.lib.homeManagerConfiguration {
          inherit pkgs;

          extraSpecialArgs = {
            inherit username home-version specialArgs latest;
          };

          modules = [ ./home.nix ];
        };
      };
    };
}
