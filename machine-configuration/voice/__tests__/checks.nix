{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../hey-bot-home-manager.nix
    ../voxtype-home-manager.nix
    ../whisp-away-home-manager.nix
    ../voice-pipeline-home-manager.nix
  ];
in
{
  domain-voice-hey-bot-options =
    mkEvalCheck "domain-voice-hey-bot-options" (builtins.hasAttr "hey-bot" cfg.services)
      "hey-bot options should be declared";
}
