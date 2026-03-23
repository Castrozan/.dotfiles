{ pkgs, ... }:
let
  hyprlandPythonLibraryPath = ./scripts/windows/lib;

  daemonPackage =
    let
      pythonSource = pkgs.writeText "hypr-maximize-focus-daemon-source.py" (
        builtins.readFile ./scripts/windows/maximize_focus_daemon.py
      );
    in
    pkgs.writeShellScriptBin "hypr-maximize-focus-daemon" ''
      export PYTHONPATH="${hyprlandPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  systemd.user.services.hypr-maximize-focus-daemon = {
    Unit = {
      Description = "Hyprland maximize focus daemon";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };
    Service = {
      ExecStart = "${daemonPackage}/bin/hypr-maximize-focus-daemon";
      Restart = "on-failure";
      RestartSec = 2;
    };
  };
}
