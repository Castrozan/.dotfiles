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
    ../fonts.nix
    ../fuzzel.nix
    ../clipse.nix
  ];

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;
in
{
  domain-desktop-fontconfig-enabled =
    mkEvalCheck "domain-desktop-fontconfig-enabled" cfg.fonts.fontconfig.enable
      "fontconfig should be enabled";

  domain-desktop-fuzzel-enabled =
    mkEvalCheck "domain-desktop-fuzzel-enabled" cfg.programs.fuzzel.enable
      "fuzzel launcher should be enabled";

  domain-desktop-clipse-service-config = mkEvalCheck "domain-desktop-clipse-service-config" (
    hasService "clipse" && hasXdgConfig "clipse/config.json"
  ) "clipse should have service and config";
}
