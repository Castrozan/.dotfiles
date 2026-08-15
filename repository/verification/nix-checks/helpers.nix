{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  mkEvalCheck =
    name: assertion: message:
    if assertion then
      pkgs.runCommandLocal "check-${name}" { } "touch $out"
    else
      builtins.throw "CHECK FAILED [${name}]: ${message}";

  mkEvalCheckGroup =
    prefix: checks:
    lib.mapAttrs' (
      name: check:
      lib.nameValuePair "${prefix}-${name}" (
        mkEvalCheck "${prefix}-${name}" check.assertion check.message
      )
    ) checks;

  # Every test configuration needs `unstable` and `latest` for the system it targets. Instantiating
  # them inside the builder below re-imported both channels once per call site, so the check suite
  # paid for hundreds of nixpkgs instantiations. Keyed attribute sets are forced once and reused.
  testSystems = lib.unique [
    "x86_64-linux"
    "aarch64-darwin"
    pkgs.stdenv.hostPlatform.system
  ];

  channelPkgsBySystem =
    channel:
    lib.genAttrs testSystems (
      system:
      import channel {
        inherit system;
        config.allowUnfree = true;
      }
    );

  unstableTestPkgs = channelPkgsBySystem inputs.nixpkgs-unstable;
  latestTestPkgs = channelPkgsBySystem inputs.nixpkgs-latest;

  homeManagerTestConfigurationForSystemPkgs =
    systemDouble: systemPkgs: hostname: modules:
    (inputs.home-manager.lib.homeManagerConfiguration {
      pkgs = systemPkgs;
      extraSpecialArgs = {
        inherit inputs;
        unstable = unstableTestPkgs.${systemDouble};
        latest = latestTestPkgs.${systemDouble};
        isNixOS = false;
        isDarwin = false;
        username = "test";
        inherit
          hostname
          nixpkgs-version
          home-version
          ;
      };
      modules = [
        ../../../machine-configuration/operating-system/health-check/health-check-home-manager.nix
        {
          home = {
            username = "test";
            homeDirectory = "/home/test";
            stateVersion = home-version;
          };
        }
      ]
      ++ modules;
    }).config;

  linuxTestPkgs = import inputs.nixpkgs {
    system = "x86_64-linux";
    config.allowUnfree = true;
  };

  homeManagerTestConfiguration =
    homeManagerTestConfigurationForSystemPkgs "x86_64-linux" linuxTestPkgs
      "test";

  homeManagerTestConfigurationForLinuxHost = homeManagerTestConfigurationForSystemPkgs "x86_64-linux" linuxTestPkgs;

  darwinTestPkgs = import inputs.nixpkgs {
    system = "aarch64-darwin";
    config.allowUnfree = true;
  };

  homeManagerTestConfigurationForDarwin =
    homeManagerTestConfigurationForSystemPkgs "aarch64-darwin" darwinTestPkgs
      "test";

  homeManagerTestConfigurationForDarwinHost = homeManagerTestConfigurationForSystemPkgs "aarch64-darwin" darwinTestPkgs;

  homeManagerTestConfigurationForEvaluatingSystem =
    homeManagerTestConfigurationForSystemPkgs pkgs.stdenv.hostPlatform.system pkgs
      "test";
in
{
  inherit
    mkEvalCheck
    mkEvalCheckGroup
    homeManagerTestConfiguration
    homeManagerTestConfigurationForDarwin
    homeManagerTestConfigurationForDarwinHost
    homeManagerTestConfigurationForLinuxHost
    homeManagerTestConfigurationForEvaluatingSystem
    ;
  stateVersion = home-version;
}
