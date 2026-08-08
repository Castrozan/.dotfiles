inputs@{ self, ... }:
let
  release = "25.11";
  linux = "x86_64-linux";
  darwin = "aarch64-darwin";

  nixosMachineFactory = import ./nixos-machine-factory.nix {
    inherit inputs release;
    system = linux;
  };
  darwinMachineFactory = import ./darwin-machine-factory.nix {
    inherit inputs release;
    system = darwin;
  };
in
{
  nixosConfigurations.chise = nixosMachineFactory {
    hostname = "chise";
    username = "zanoni";
  };

  darwinConfigurations.rin = darwinMachineFactory {
    hostname = "rin";
    username = "lucas.zanoni";
  };
  darwinConfigurations.kira = darwinMachineFactory {
    hostname = "kira";
    username = "lucas.zanoni";
  };

  homeManagerModules = import ./home-manager-modules.nix;

  checks = import ./checks.nix {
    inherit inputs self release;
    systems = [
      linux
      darwin
    ];
  };
}
