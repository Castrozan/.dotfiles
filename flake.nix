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

    # External flakes to be available for dependency injection
    # Tag-based (stable releases)
    tui-notifier.url = "github:castrozan/tui-notifier/1.0.1";
    systemd-manager-tui.url = "github:matheus-git/systemd-manager-tui";
    systemd-manager-tui.inputs.nixpkgs.follows = "nixpkgs";
    readItNow-rc.url = "github:castrozan/readItNow-rc/1.1.0";
    opencode.url = "github:anomalyco/opencode/v1.1.36";
    zed-editor.url = "github:zed-industries/zed/v0.218.5";
    devenv.url = "github:cachix/devenv/v1.11.2";
    # Branch/default (actively maintained)
    bluetui.url = "github:castrozan/bluetui/v0.9.1";
    cbonsai.url = "github:castrozan/cbonsai";
    cmatrix.url = "github:castrozan/cmatrix";
    tuisvn.url = "github:castrozan/tuisvn";
    install-nothing.url = "github:castrozan/install-nothing";
    nixgl.url = "github:nix-community/nixGL";
    agenix.url = "github:ryantm/agenix";

    voxtype.url = "github:peteonrails/voxtype";
    hyprland.url = "github:hyprwm/Hyprland/v0.53.0";
    hyprshell = {
      url = "github:H3rmt/hyprshell/hyprshell-release";
      inputs.hyprland.follows = "hyprland";
    };
    spicetify-nix.url = "github:Gerg-L/spicetify-nix";
    spicetify-nix.inputs.nixpkgs.follows = "nixpkgs";
  };

  # Outputs are what this flake provides, such as pkgs and system configurations
  outputs =
    inputs@{
      nixpkgs,
      nixpkgs-unstable,
      nixpkgs-latest,
      home-manager,
      ...
    }:
    # let in notation to declare local variables for output scope
    let
      system = "x86_64-linux"; # linux system architecture
      home-version = "25.11";
      nixpkgs-version = "25.11";
      # Configure nixpkgs then attribute it to pkgs at the same time
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
          # Function definition
          mkHomeConfigFor = username: {
            "${username}@${system}" = home-manager.lib.homeManagerConfiguration {
              inherit pkgs;

              extraSpecialArgs = specialArgsBase // {
                inherit username;
                isNixOS = false;
              };

              modules = [ ./users/${username}/home.nix ];
            };
          };
        in
        # Function call with arguments
        mkHomeConfigFor "lucas.zanoni";

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
            inherit system;

            modules = [
              ./hosts/dellg15
              ./users/${username}/nixos.nix
              home-manager.nixosModules.home-manager
              (import ./users/${username}/nixos-home-config.nix)
            ];
          };
        };
    };
}
