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
    ../firefox.nix
    ../chrome-global.nix
  ];
in
{
  domain-browser-firefox-enabled =
    mkEvalCheck "domain-browser-firefox-enabled" cfg.programs.firefox.enable
      "firefox should be enabled";

  domain-browser-chrome-desktop-entry =
    mkEvalCheck "domain-browser-chrome-desktop-entry"
      (builtins.hasAttr "chrome-global" cfg.xdg.desktopEntries)
      "chrome desktop entry should be registered";
}
