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

  homeManagerTestConfiguration =
    modules:
    (inputs.home-manager.lib.homeManagerConfiguration {
      inherit pkgs;
      extraSpecialArgs = {
        inherit inputs;
        unstable = import inputs.nixpkgs-unstable {
          system = "x86_64-linux";
          config.allowUnfree = true;
        };
        latest = import inputs.nixpkgs-latest {
          system = "x86_64-linux";
          config.allowUnfree = true;
        };
        isNixOS = false;
        username = "test";
        inherit nixpkgs-version home-version;
      };
      modules = [
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = home-version;
        }
      ]
      ++ modules;
    }).config;
in
{
  inherit mkEvalCheck mkEvalCheckGroup homeManagerTestConfiguration;
  stateVersion = home-version;
}
