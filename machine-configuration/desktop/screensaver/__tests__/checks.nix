{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  linuxCfg = helpers.homeManagerTestConfiguration [ ../screensaver-home-manager.nix ];
  darwinCfg = helpers.homeManagerTestConfigurationForDarwin [ ../screensaver-home-manager.nix ];

  aliasesContent = builtins.readFile ../../../terminal/shell/bash/program-configuration/aliases.sh;

  packageIsInstalled = name: cfg: builtins.any (pkg: (pkg.name or "") == name) cfg.home.packages;

  linuxInstallsHerdrScreensaver = packageIsInstalled "herdr-screensaver" linuxCfg;
  darwinInstallsHerdrScreensaver = packageIsInstalled "herdr-screensaver" darwinCfg;
  aliasGuardedByCommandExistence = lib.hasInfix "command -v herdr-screensaver" aliasesContent;

  darwinInstallsAmbientCanvas = packageIsInstalled "ambient-canvas" darwinCfg;
  linuxInstallsAmbientCanvas = packageIsInstalled "ambient-canvas" linuxCfg;
  darwinInstallsAmbientCanvasLoopRenderer = packageIsInstalled "ambient-canvas-render" darwinCfg;
  linuxInstallsAmbientCanvasLoopRenderer = packageIsInstalled "ambient-canvas-render" linuxCfg;

  darwinCompilesAmbientCanvasNativePlayer = darwinCfg.home.activation ? compileAmbientCanvasPlayer;
  linuxCompilesAmbientCanvasNativePlayer = linuxCfg.home.activation ? compileAmbientCanvasPlayer;

  linuxInstallsAmbientCanvasMpvPlayer =
    linuxCfg.home.file ? "${linuxCfg.home.homeDirectory}/.local/bin/ᓚᘏᗢ";
  darwinInstallsAmbientCanvasMpvPlayer =
    darwinCfg.home.file ? "${darwinCfg.home.homeDirectory}/.local/bin/ᓚᘏᗢ";

  linuxWiresAmbientCanvasKeepAlive =
    (linuxCfg.systemd.user.services ? ambient-canvas)
    && (linuxCfg.systemd.user.timers ? ambient-canvas);
  darwinWiresAmbientCanvasKeepAlive = darwinCfg.launchd.agents ? ambient-canvas;
in
{
  domain-screensaver-herdr-launcher-installed-on-linux =
    mkEvalCheck "domain-screensaver-herdr-launcher-installed-on-linux" linuxInstallsHerdrScreensaver
      "the herdr terminal screensaver (herdr-screensaver) must be installed on Linux alongside the ambient-canvas player, which is the primary Linux screensaver";

  domain-screensaver-herdr-launcher-gated-out-on-darwin =
    mkEvalCheck "domain-screensaver-herdr-launcher-gated-out-on-darwin"
      (!darwinInstallsHerdrScreensaver)
      "herdr-screensaver must not be installed on darwin, whose screensaver is the native pre-recorded ambient-canvas loop player: the herdr grid repaints in wezterm and pins the interactive GUI at roughly half a core even when parked off-screen";

  domain-screensaver-alias-wired-to-herdr-screensaver-package =
    mkEvalCheck "domain-screensaver-alias-wired-to-herdr-screensaver-package"
      (linuxInstallsHerdrScreensaver && lib.hasInfix "alias h='herdr-screensaver'" aliasesContent)
      "the h alias defined in the terminal domain must invoke herdr-screensaver and that command must be registered as a home package on Linux, or typing h runs a missing binary";

  domain-screensaver-alias-does-not-dangle-on-darwin =
    mkEvalCheck "domain-screensaver-alias-does-not-dangle-on-darwin"
      (darwinInstallsHerdrScreensaver || aliasGuardedByCommandExistence)
      "aliases.sh defines h for every platform that sources it, but herdr-screensaver installs only on Linux, so on darwin the alias must be guarded by command -v herdr-screensaver or typing h runs a missing binary";

  domain-screensaver-ambient-canvas-launcher-installed-on-both =
    mkEvalCheck "domain-screensaver-ambient-canvas-launcher-installed-on-both"
      (darwinInstallsAmbientCanvas && linuxInstallsAmbientCanvas)
      "the ambient-canvas launcher drives the pre-recorded loop on both platforms, so it must be a home package on darwin and on Linux";

  domain-screensaver-ambient-canvas-loop-renderer-installed-on-both =
    mkEvalCheck "domain-screensaver-ambient-canvas-loop-renderer-installed-on-both"
      (darwinInstallsAmbientCanvasLoopRenderer && linuxInstallsAmbientCanvasLoopRenderer)
      "the ambient-canvas-render command regenerates the pre-recorded loop video from the web scenes and is the shared recording pipeline on both platforms, so it must install on darwin and on Linux";

  domain-screensaver-ambient-canvas-native-player-compiled-on-darwin-only =
    mkEvalCheck "domain-screensaver-ambient-canvas-native-player-compiled-on-darwin-only"
      (darwinCompilesAmbientCanvasNativePlayer && !linuxCompilesAmbientCanvasNativePlayer)
      "the ambient-canvas-player Swift AVPlayer binary is the darwin playback backend, so its compile activation must run only on darwin, where swiftc and AVFoundation exist, and never on Linux, whose backend is the mpv driver";

  domain-screensaver-ambient-canvas-mpv-player-installed-on-linux-only =
    mkEvalCheck "domain-screensaver-ambient-canvas-mpv-player-installed-on-linux-only"
      (linuxInstallsAmbientCanvasMpvPlayer && !darwinInstallsAmbientCanvasMpvPlayer)
      "the mpv-based player must be installed as ~/.local/bin/ᓚᘏᗢ only on Linux, where it replaces the Swift AVPlayer as the recorded-loop playback backend";

  domain-screensaver-ambient-canvas-keep-alive-wired-per-platform =
    mkEvalCheck "domain-screensaver-ambient-canvas-keep-alive-wired-per-platform"
      (linuxWiresAmbientCanvasKeepAlive && darwinWiresAmbientCanvasKeepAlive)
      "the ambient-canvas keep-alive must be wired on every platform: a systemd user service on Linux and a launchd agent on darwin, or a died player is never respawned";
}
