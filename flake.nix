{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.
  '';

  inputs = {
    # Core
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";

    # Flake framework
    flake-parts.url = "github:hercules-ci/flake-parts";

    home-manager = {
      url = "github:nix-community/home-manager/release-25.11";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    # External flakes - Tag-based (stable releases)
    tui-notifier.url = "github:castrozan/tui-notifier/1.0.1";
    readItNow-rc.url = "github:castrozan/readItNow-rc/1.1.0";
    opencode.url = "github:anomalyco/opencode/v1.1.36";
    zed-editor.url = "github:zed-industries/zed/v0.218.5";
    devenv.url = "github:cachix/devenv/v1.9.2";

    # External flakes - Branch/default (actively maintained)
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
  };

  outputs =
    inputs@{
      flake-parts,
      nixpkgs,
      home-manager,
      ...
    }:
    let
      # Shared configuration
      system = "x86_64-linux";
      home-version = "25.11";
      nixpkgs-version = "25.11";

      mkPkgs =
        nixpkgs:
        import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

      pkgs = mkPkgs nixpkgs;
      unstable = mkPkgs inputs.nixpkgs-unstable;
      latest = mkPkgs inputs.nixpkgs-latest;

      specialArgsBase = {
        inherit
          inputs
          unstable
          latest
          home-version
          nixpkgs-version
          ;
      };

      # Helper to create home-manager configuration
      mkHomeConfig =
        username:
        home-manager.lib.homeManagerConfiguration {
          inherit pkgs;
          extraSpecialArgs = specialArgsBase // {
            inherit username;
          };
          modules = [
            ./configurations/home/${username}.nix
          ];
        };

      # Helper to create NixOS configuration
      mkNixosConfig =
        { hostname, username }:
        nixpkgs.lib.nixosSystem {
          inherit system;
          specialArgs = specialArgsBase // {
            inherit username;
          };
          modules = [
            ./configurations/nixos/${hostname}.nix
            home-manager.nixosModules.home-manager
            {
              home-manager = {
                useGlobalPkgs = true;
                useUserPackages = true;
                backupFileExtension = "backup";
                extraSpecialArgs = specialArgsBase // {
                  inherit username;
                };
                users.${username} = import ./configurations/home/${username}.nix;
              };
            }
          ];
        };
    in
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" ];

      flake = {
        homeConfigurations = {
          "lucas.zanoni@${system}" = mkHomeConfig "lucas.zanoni";
        };

        nixosConfigurations = {
          zanoni = mkNixosConfig {
            hostname = "zanoni";
            username = "zanoni";
          };
        };
      };
    };
}
