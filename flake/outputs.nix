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

  prebuiltFishFromUpstreamReleaseThatStillPassesMacOSTahoeCodeSigningAtExec =
    pkgsForDarwin: import ../lib/fish-prebuilt-darwin.nix { pkgs = pkgsForDarwin; };

  workingFishOnDarwinForMacOSCodeSigningEnforcementOverlay =
    final: prev:
    if prev.stdenv.hostPlatform.isDarwin then
      {
        fish = prebuiltFishFromUpstreamReleaseThatStillPassesMacOSTahoeCodeSigningAtExec prev;
      }
    else
      { };

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
  # homeConfigurations.<machineAlias> is a standalone home-manager
  # configuration. Anime alias as key (jojo, ...); username is set via
  # extraSpecialArgs. ./bin/rebuild applies it.
  homeConfigurations = {
    jojo = home-manager.lib.homeManagerConfiguration {
      inherit pkgs;

      extraSpecialArgs = specialArgsBase // {
        username = "lucas.zanoni";
        hostname = "jojo";
        isNixOS = false;
        isDarwin = false;
      };

      modules = [ ../home/hosts/linux/jojo.nix ];
    };
  };

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
    darwinSystemOverlays = [ workingFishOnDarwinForMacOSCodeSigningEnforcementOverlay ];
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
