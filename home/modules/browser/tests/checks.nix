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

  domain-browser-chrome-desktop-entry = mkEvalCheck "domain-browser-chrome-desktop-entry" (
    cfg.xdg.dataFile ? "applications/chrome-global.desktop"
  ) "chrome desktop entry should be in XDG_DATA_HOME";

  domain-browser-chrome-no-remote-debugging-flag =
    let
      desktopSource = cfg.xdg.dataFile."applications/chrome-global.desktop".source or "";
    in
    mkEvalCheck "domain-browser-chrome-no-remote-debugging-flag"
      (!lib.hasInfix "--remote-debugging-port" (builtins.toString desktopSource))
      "chrome-global desktop entry should not have --remote-debugging-port (bare Chrome for autoConnect stealth)";
}
