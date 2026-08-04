{
  helpers,
  pkgs,
  lib,
  ...
}:
let
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
