{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
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
    ../../../linux/desktop/fuzzel.nix
    ../../../linux/desktop/clipse.nix
  ];

  hasService = name: builtins.hasAttr name cfg.systemd.user.services;
  hasXdgConfig = name: builtins.hasAttr name cfg.xdg.configFile;

  darwinThemingCfg = helpers.homeManagerTestConfigurationForDarwin [
    ../theming/darwin
  ];
  darwinThemingPackageNames = map (
    package: package.name or package.pname or "unknown"
  ) darwinThemingCfg.home.packages;
  darwinThemingHasPackageMatching =
    pattern: builtins.any (name: builtins.match pattern name != null) darwinThemingPackageNames;
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

  domain-desktop-theming-wallpaper-derived-regeneration-command-darwin =
    mkEvalCheck "domain-desktop-theming-wallpaper-derived-regeneration-command-darwin"
      (darwinThemingHasPackageMatching ".*theme-regenerate-wallpaper-derived-colors.*")
      "the darwin theming module must install the wallpaper-derived colors regeneration command the rebuild wrapper invokes";
}
