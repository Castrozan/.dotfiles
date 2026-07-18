{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  linuxCfg = helpers.homeManagerTestConfiguration [ ../default.nix ];
  darwinCfg = helpers.homeManagerTestConfigurationForDarwin [ ../default.nix ];

  aliasesContent = builtins.readFile ../../../terminal/shell/aliases.sh;

  packageIsInstalled = name: cfg: builtins.any (pkg: (pkg.name or "") == name) cfg.home.packages;

  linuxInstallsHerdrScreensaver = packageIsInstalled "herdr-screensaver" linuxCfg;
  darwinInstallsHerdrScreensaver = packageIsInstalled "herdr-screensaver" darwinCfg;
  aliasGuardedByCommandExistence = lib.hasInfix "command -v herdr-screensaver" aliasesContent;
in
{
  domain-screensaver-herdr-launcher-installed-on-linux =
    mkEvalCheck "domain-screensaver-herdr-launcher-installed-on-linux" linuxInstallsHerdrScreensaver
      "the herdr terminal screensaver (herdr-screensaver) must be installed on Linux, whose screensaver is the herdr terminal grid";

  domain-screensaver-herdr-launcher-gated-out-on-darwin =
    mkEvalCheck "domain-screensaver-herdr-launcher-gated-out-on-darwin"
      (!darwinInstallsHerdrScreensaver)
      "herdr-screensaver must not be installed on darwin, whose screensaver is the GPU-isolated Chrome ambient-canvas: the herdr grid repaints in wezterm and pins the interactive GUI at roughly half a core even when parked off-screen";

  domain-screensaver-alias-wired-to-herdr-screensaver-package =
    mkEvalCheck "domain-screensaver-alias-wired-to-herdr-screensaver-package"
      (linuxInstallsHerdrScreensaver && lib.hasInfix "alias h='herdr-screensaver'" aliasesContent)
      "the h alias defined in the terminal domain must invoke herdr-screensaver and that command must be registered as a home package on Linux, or typing h runs a missing binary";

  domain-screensaver-alias-does-not-dangle-on-darwin =
    mkEvalCheck "domain-screensaver-alias-does-not-dangle-on-darwin"
      (darwinInstallsHerdrScreensaver || aliasGuardedByCommandExistence)
      "aliases.sh defines h for every platform that sources it, but herdr-screensaver installs only on Linux, so on darwin the alias must be guarded by command -v herdr-screensaver or typing h runs a missing binary";

  domain-screensaver-ambient-canvas-is-darwin-only =
    mkEvalCheck "domain-screensaver-ambient-canvas-is-darwin-only"
      (packageIsInstalled "ambient-canvas" darwinCfg && !(packageIsInstalled "ambient-canvas" linuxCfg))
      "the Chrome ambient-canvas screensaver must build only on darwin, where its GPU-isolated window never touches the wezterm frame budget, and never on Linux, where the herdr grid is used instead";
}
