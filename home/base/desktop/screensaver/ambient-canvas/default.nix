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

  ambientCanvasScreensaverLauncher = pkgs.writeShellScriptBin "ambient-canvas" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/ensure_ambient_canvas_screensaver.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      "$@"
  '';

  ambientCanvasLoopRenderer = pkgs.writeShellScriptBin "ambient-canvas-render" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/render_ambient_canvas_loop.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      "$@"
  '';
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    home.packages = [
      ambientCanvasScreensaverLauncher
      ambientCanvasLoopRenderer
    ];

    home.activation.ensureAmbientCanvasStateDirectory = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run mkdir -p ${lib.escapeShellArg ambientCanvasStateDirectory}
    '';

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
