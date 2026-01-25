{ pkgs, ... }:
let
  calendarPythonEnv = pkgs.python3.withPackages (ps: [
    ps.pygobject3
    ps.pycairo
  ]);

  calendar-popup = pkgs.writeShellScriptBin "calendar-popup" ''
    export GI_TYPELIB_PATH="${pkgs.gtk3}/lib/girepository-1.0:${pkgs.gdk-pixbuf}/lib/girepository-1.0:${pkgs.pango}/lib/girepository-1.0''${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}"
    export LD_LIBRARY_PATH="${pkgs.gtk3}/lib:${pkgs.gdk-pixbuf}/lib''${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    exec ${calendarPythonEnv}/bin/python3 ~/.config/waybar/calendar-popup.py "$@"
  '';

  calendar-toggle = pkgs.writeShellScriptBin "calendar-toggle" ''
    if ${pkgs.procps}/bin/pkill -f "calendar-popup.py"; then
        exit 0
    else
        ${calendar-popup}/bin/calendar-popup &
    fi
  '';
in
{
  home = {
    file.".config/waybar/calendar-popup.py".source = ../../../.config/waybar/calendar-popup.py;

    packages = [ calendar-toggle ];
  };
}
