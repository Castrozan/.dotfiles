{
  pkgs,
  lib,
  config,
  ...
}:
let
  ambientCanvasWebRoot = ./web;
  ambientCanvasLauncherSource = pkgs.writeText "launch-ambient-canvas.py" (
    builtins.readFile ./scripts/launch_ambient_canvas.py
  );
  ambientCanvasLauncher = pkgs.writeShellScriptBin "ambient-canvas" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasWebRoot}/index.html"
    exec ${pkgs.python312}/bin/python3 ${ambientCanvasLauncherSource} "$@"
  '';
  ambientCanvasStateDirectory = "${config.home.homeDirectory}/.local/state/ambient-canvas";
  relaunchAmbientCanvasIfNotRunning = pkgs.writeShellScript "relaunch-ambient-canvas-if-not-running" ''
    if ! /usr/bin/pgrep -f "ambient-canvas/profile" >/dev/null 2>&1; then
      exec ${ambientCanvasLauncher}/bin/ambient-canvas
    fi
  '';
in
{
  config = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
    home.packages = [ ambientCanvasLauncher ];

    home.activation.ensureAmbientCanvasStateDirectory = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run mkdir -p ${lib.escapeShellArg ambientCanvasStateDirectory}
    '';

    launchd.agents.ambient-canvas = {
      enable = true;
      config = {
        Label = "com.dotfiles.ambient-canvas";
        ProgramArguments = [ "${relaunchAmbientCanvasIfNotRunning}" ];
        RunAtLoad = true;
        StartInterval = 30;
        StandardOutPath = "${ambientCanvasStateDirectory}/keep-alive.log";
        StandardErrorPath = "${ambientCanvasStateDirectory}/keep-alive.log";
      };
    };
  };
}
