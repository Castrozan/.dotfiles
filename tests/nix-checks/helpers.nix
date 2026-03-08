{
  pkgs,
  lib,
  inputs,
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
        nixpkgs-version = "25.11";
        home-version = "25.11";
      };
      modules = [
        {
          home.username = "test";
          home.homeDirectory = "/home/test";
          home.stateVersion = "25.11";
        }
      ]
      ++ modules;
    }).config;
in
{
  inherit mkEvalCheck mkEvalCheckGroup homeManagerTestConfiguration;
}
