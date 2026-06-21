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

  homeManagerTestConfigurationForSystemPkgs =
    systemDouble: systemPkgs: modules:
    (inputs.home-manager.lib.homeManagerConfiguration {
      pkgs = systemPkgs;
      extraSpecialArgs = {
        inherit inputs;
        unstable = import inputs.nixpkgs-unstable {
          system = systemDouble;
          config.allowUnfree = true;
        };
        latest = import inputs.nixpkgs-latest {
          system = systemDouble;
          config.allowUnfree = true;
        };
        isNixOS = false;
        username = "test";
        hostname = "test";
        inherit nixpkgs-version home-version;
      };
      modules = [
        ../../home/base/system/health-check
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

  homeManagerTestConfiguration = homeManagerTestConfigurationForSystemPkgs "x86_64-linux" pkgs;

  homeManagerTestConfigurationForDarwin = homeManagerTestConfigurationForSystemPkgs "aarch64-darwin" (
    import inputs.nixpkgs {
      system = "aarch64-darwin";
      config.allowUnfree = true;
    }
  );
in
{
  inherit
    mkEvalCheck
    mkEvalCheckGroup
    homeManagerTestConfiguration
    homeManagerTestConfigurationForDarwin
    ;
  stateVersion = home-version;
}
