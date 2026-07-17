{ pkgs, ... }:
let
  ambientCanvasWebRoot = ./web;
  ambientCanvasLauncherSource = pkgs.writeText "launch-ambient-canvas.py" (
    builtins.readFile ./scripts/launch_ambient_canvas.py
  );
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "ambient-canvas" ''
      export AMBIENT_CANVAS_INDEX="${ambientCanvasWebRoot}/index.html"
      exec ${pkgs.python312}/bin/python3 ${ambientCanvasLauncherSource} "$@"
    '')
  ];
}
