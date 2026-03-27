{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.
  '';

  # Inputs are used to declare package definitions and modules to fetch from the internet
  inputs = {
    # For stable packages definitions
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    # For packages not yet in nixpkgs
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    # For latest bleeding edge packages - daily* updated with: $ nix flake update nixpkgs-latest
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager/release-25.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    # Tag-pinned — keep own nixpkgs
    tui-notifier.url = "github:castrozan/tui-notifier/1.0.1";
    systemd-manager-tui.url = "github:matheus-git/systemd-manager-tui";
    systemd-manager-tui.inputs.nixpkgs.follows = "nixpkgs";
    readItNow-rc.url = "github:castrozan/readItNow-rc/1.1.0";
    opencode.url = "github:anomalyco/opencode/v1.3.3";
    devenv.url = "github:cachix/devenv/v1.11.2";
    bluetui.url = "github:castrozan/bluetui/v0.9.1";
    hyprland.url = "github:hyprwm/Hyprland/v0.54.2";
    # Branch/default own forks — follow nixpkgs
    cbonsai.url = "github:castrozan/cbonsai";
    cbonsai.inputs.nixpkgs.follows = "nixpkgs";
    cmatrix.url = "github:castrozan/cmatrix";
    cmatrix.inputs.nixpkgs.follows = "nixpkgs";
    tuisvn.url = "github:castrozan/tuisvn";
    tuisvn.inputs.nixpkgs.follows = "nixpkgs";
    install-nothing.url = "github:castrozan/install-nothing";
    install-nothing.inputs.nixpkgs.follows = "nixpkgs";
    openclaw-mesh.url = "github:castrozan/openclaw-mesh";
    openclaw-mesh.inputs.nixpkgs.follows = "nixpkgs";
    lazygit.url = "github:Castrozan/lazygit";
    lazygit.inputs.nixpkgs.follows = "nixpkgs";
    viu.url = "github:Castrozan/viu";
    viu.inputs.nixpkgs.follows = "nixpkgs";
    voice-pipeline.url = "github:castrozan/voice-pipeline";
    voice-pipeline.inputs.nixpkgs.follows = "nixpkgs";
    # Well-maintained, nixpkgs-agnostic
    nixgl.url = "github:nix-community/nixGL";
    nixgl.inputs.nixpkgs.follows = "nixpkgs";
    agenix.url = "github:ryantm/agenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";
    # Third-party — keep own nixpkgs
    voxtype.url = "github:peteonrails/voxtype";
    whisp-away.url = "github:madjinn/whisp-away";
    google-workspace-cli.url = "github:googleworkspace/cli";
  };

  # Outputs are what this flake provides, such as pkgs and system configurations
  outputs =
    inputs@{
      self,
      nixpkgs,
      nixpkgs-unstable,
      nixpkgs-latest,
      home-manager,
      ...
    }:
    # let in notation to declare local variables for output scope
    let
      linuxSystem = "x86_64-linux";
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
      # homeConfigurations.${username}@${system}
      # is a standalone home manager configuration for a user and system architecture
      # ./bin/rebuild for how to apply the flake
      homeConfigurations =
        let
          mkLinuxHomeConfigFor = username: {
            "${username}@${linuxSystem}" = home-manager.lib.homeManagerConfiguration {
              inherit pkgs;

              extraSpecialArgs = specialArgsBase // {
                inherit username;
                isNixOS = false;
              };

              modules = [ ./users/${username}/home.nix ];
            };
          };
        in
        mkLinuxHomeConfigFor "lucas.zanoni";

      # nixosConfigurations.${username} is a NixOS system configuration for a user
      # ./bin/rebuild for how to apply
      nixosConfigurations =
        let
          username = "zanoni";
          specialArgs = specialArgsBase // {
            inherit username;
            isNixOS = true;
          };
        in
        {
          "${username}" = nixpkgs.lib.nixosSystem {
            inherit specialArgs;
            system = linuxSystem;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix
              home-manager.nixosModules.home-manager
              (import ./users/${username}/nixos-home-config.nix)
            ];
          };
        };

      homeManagerModules = {
        openclaw = ./home/modules/openclaw;
        claude-code = ./home/modules/claude;
        codex = ./home/modules/codex;
        default = {
          imports = [
            ./home/modules/claude
            ./home/modules/codex
          ];
        };
      };

      checks.${linuxSystem} = import ./tests/nix-checks {
        inherit
          pkgs
          inputs
          self
          nixpkgs-version
          home-version
          ;
        inherit (nixpkgs) lib;
      };
    };
}
