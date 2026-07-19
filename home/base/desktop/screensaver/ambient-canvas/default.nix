{
  pkgs,
  lib,
  config,
  ...
}:
let
  ambientCanvasWebRoot = ./web;
  ambientCanvasIndexFile = "${ambientCanvasWebRoot}/index.html";
  ambientCanvasMediaScriptsDirectory = ./scripts/ambient_canvas_media;
  ambientCanvasStateDirectory = "${config.home.homeDirectory}/.local/state/ambient-canvas";
  ambientCanvasSourceIdentifier = "${ambientCanvasWebRoot}";
  ambientCanvasPlayerBinaryPath = "${config.home.homeDirectory}/.local/bin/ambient-canvas-player";

  ambientCanvasSceneVideoDownloaderPath = lib.makeBinPath [ pkgs.yt-dlp ];

  ambientCanvasScreensaverLauncher = pkgs.writeShellScriptBin "ambient-canvas" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    export PATH="${ambientCanvasSceneVideoDownloaderPath}:$PATH"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/ensure_ambient_canvas_screensaver.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      --player-binary "${ambientCanvasPlayerBinaryPath}" \
      "$@"
  '';

  ambientCanvasLoopRenderer = pkgs.writeShellScriptBin "ambient-canvas-render" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    export PATH="${ambientCanvasSceneVideoDownloaderPath}:$PATH"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/render_ambient_canvas_loop.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      "$@"
  '';
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    home = {
      packages = [
        ambientCanvasScreensaverLauncher
        ambientCanvasLoopRenderer
      ];

      activation.ensureAmbientCanvasStateDirectory = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        run mkdir -p ${lib.escapeShellArg ambientCanvasStateDirectory}
      '';

      activation.compileAmbientCanvasPlayer = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        export AMBIENT_CANVAS_PLAYER_BINARY_PATH=${lib.escapeShellArg ambientCanvasPlayerBinaryPath}
        export AMBIENT_CANVAS_PLAYER_SOURCES_DIR=${./swift-sources}
        export AMBIENT_CANVAS_PLAYER_COMPILE_RECIPE_HASH=${builtins.hashFile "sha256" ./compile-player.sh}
        ${builtins.readFile ./compile-player.sh}
      '';
    };

    launchd.agents.ambient-canvas = {
      enable = true;
      config = {
        Label = "com.dotfiles.ambient-canvas";
        ProgramArguments = [ "${ambientCanvasScreensaverLauncher}/bin/ambient-canvas" ];
        RunAtLoad = true;
        StartInterval = 30;
        StandardOutPath = "${ambientCanvasStateDirectory}/keep-alive.log";
        StandardErrorPath = "${ambientCanvasStateDirectory}/keep-alive.log";
      };
    };
  };
}
