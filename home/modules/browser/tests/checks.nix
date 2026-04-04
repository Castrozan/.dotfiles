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

  domain-browser-chrome-no-remote-debugging-flag =
    mkEvalCheck "domain-browser-chrome-no-remote-debugging-flag"
      (!lib.hasInfix "--remote-debugging-port" (cfg.xdg.desktopEntries.chrome-global.exec or ""))
      "chrome-global desktop entry should not have --remote-debugging-port (bare Chrome for autoConnect stealth)";
}
