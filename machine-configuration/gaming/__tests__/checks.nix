{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    ../vesktop/vesktop-home-manager.nix
    ../../terminal/visual-effects/cbonsai/cbonsai-chise-home-manager.nix
    ../install-nothing/install-nothing-home-manager.nix
  ];

  hasFile = name: builtins.hasAttr name cfg.home.file;
in
{
  domain-gaming-vesktop-config =
    mkEvalCheck "domain-gaming-vesktop-config" (hasFile ".config/vesktop/settings/settings.json")
      "vesktop config should be deployed";
}
