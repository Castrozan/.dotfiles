{ pkgs, ... }:
let
  hyprlandPythonLibraryPath = ./scripts/windows/lib;

  daemonPackage =
    let
      pythonSource = pkgs.writeText "hypr-focus-daemon-source.py" (
        builtins.readFile ./scripts/windows/focus_daemon.py
      );
    in
    pkgs.writeShellScriptBin "hypr-focus-daemon" ''
      export PYTHONPATH="${hyprlandPythonLibraryPath}:''${PYTHONPATH:-}"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  systemd.user.services.hypr-focus-daemon = {
    Unit = {
      Description = "Hyprland focus daemon";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };
    Service = {
      ExecStart = "${daemonPackage}/bin/hypr-focus-daemon";
      Restart = "on-failure";
      RestartSec = 2;
    };
    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
