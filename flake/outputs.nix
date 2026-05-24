inputs@{
  self,
  nixpkgs,
  nixpkgs-unstable,
  nixpkgs-latest,
  home-manager,
  nix-darwin,
  ...
}:
let
  linuxSystem = "x86_64-linux";
  darwinSystem = "aarch64-darwin";
  home-version = "25.11";
  nixpkgs-version = "25.11";

  mkPkgsFor = system: {
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
  };

  linux = mkPkgsFor linuxSystem;
  inherit (linux) pkgs unstable latest;

  darwin = mkPkgsFor darwinSystem;

  specialArgsBase = {
    inherit
      nixpkgs-version
      home-version
      unstable
      inputs
      latest
      ;
  };
in
{
  # homeConfigurations.${username}@${system} is a standalone home-manager
  # configuration for a user and system architecture. ./bin/rebuild applies it.
  homeConfigurations =
    let
      mkLinuxHomeConfigFor = username: {
        "${username}@${linuxSystem}" = home-manager.lib.homeManagerConfiguration {
          inherit pkgs;

          extraSpecialArgs = specialArgsBase // {
            inherit username;
            isNixOS = false;
            isDarwin = false;
          };

          modules = [ ../users/${username}/home.nix ];
        };
      };
    in
    mkLinuxHomeConfigFor "lucas.zanoni";

  nixosConfigurations = import ./nixos-configurations.nix {
    inherit
      nixpkgs
      home-manager
      linuxSystem
      specialArgsBase
      ;
  };

  darwinConfigurations = import ./darwin-configurations.nix {
    inherit
      nix-darwin
      home-manager
      darwinSystem
      specialArgsBase
      ;
    darwinPkgs = darwin;
  };

  homeManagerModules = import ./home-manager-modules.nix;

  checks.${linuxSystem} = import ../tests/nix-checks {
    inherit
      pkgs
      inputs
      self
      nixpkgs-version
      home-version
      ;
    inherit (nixpkgs) lib;
  };
}
