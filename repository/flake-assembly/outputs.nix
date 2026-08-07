inputs@{ self, ... }:
let
  release = "25.11";
  linux = "x86_64-linux";
  darwin = "aarch64-darwin";

  nixosMachine = import ./nixos-machine.nix {
    inherit inputs release;
    system = linux;
  };
  darwinMachine = import ./darwin-machine.nix {
    inherit inputs release;
    system = darwin;
  };
in
{
  nixosConfigurations.chise = nixosMachine {
    hostname = "chise";
    username = "zanoni";
  };

  darwinConfigurations.rin = darwinMachine {
    hostname = "rin";
    username = "lucas.zanoni";
  };
  darwinConfigurations.kira = darwinMachine {
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
