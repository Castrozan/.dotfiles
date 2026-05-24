{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../hey-bot.nix
    ../voxtype.nix
    ../whisp-away.nix
    ../voice-pipeline.nix
  ];
in
{
  domain-voice-hey-bot-options =
    mkEvalCheck "domain-voice-hey-bot-options" (builtins.hasAttr "hey-bot" cfg.services)
      "hey-bot options should be declared";
}
