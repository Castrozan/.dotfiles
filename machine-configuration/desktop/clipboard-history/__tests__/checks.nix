{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../clipse-home-manager.nix ];

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
in
{
  domain-desktop-clipse-service-config = mkEvalCheck "domain-desktop-clipse-service-config" (
    hasService "clipse" && hasXdgConfig "clipse/config.json"
  ) "clipse should have service and config";
}
// import ./maccy-home-manager-checks.nix {
  inherit helpers pkgs lib;
}
