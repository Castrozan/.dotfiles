{ pkgs, lib, ... }:
let
  # Wrap swaync to isolate GIO modules and prevent loading incompatible system libraries
  # Fixes CPU spin from GLIBC version mismatch with gvfs/dconf modules
  gioModuleDir = "${pkgs.glib-networking}/lib/gio/modules";

  wrappedSwaync = pkgs.symlinkJoin {
    name = "swaync-wrapped";
    paths = [ pkgs.swaynotificationcenter ];
    buildInputs = [ pkgs.makeWrapper ];
    postBuild = ''
      # Wrap binaries with GIO_MODULE_DIR
      for bin in swaync swaync-client; do
        if [ -f "$out/bin/$bin" ]; then
          wrapProgram "$out/bin/$bin" \
            --set GIO_MODULE_DIR "${gioModuleDir}"
        fi
      done

      # Patch D-Bus service file to use wrapped binary
      if [ -d "$out/share/dbus-1/services" ]; then
        for service in $out/share/dbus-1/services/*.service; do
          rm "$service"
        done
        rmdir "$out/share/dbus-1/services"
        mkdir -p "$out/share/dbus-1/services"
        cat > "$out/share/dbus-1/services/org.erikreider.swaync.service" <<EOF
      [D-BUS Service]
      Name=org.freedesktop.Notifications
      Exec=$out/bin/swaync
      SystemdService=swaync.service
      EOF
      fi
    '';
  };

  swayncStart = pkgs.writeShellScript "swaync-start" ''
    # Set GIO_MODULE_DIR to prevent loading incompatible system GIO modules
    export GIO_MODULE_DIR="${gioModuleDir}"

    THEME_CSS="$HOME/.config/omarchy/current/theme/swaync.css"
    if [[ -f "$THEME_CSS" ]]; then
      exec ${wrappedSwaync}/bin/swaync --style "$THEME_CSS"
    else
      exec ${wrappedSwaync}/bin/swaync
    fi
  '';
in
{
  home.packages = [ wrappedSwaync ];

  # Set GIO_MODULE_DIR session-wide to prevent ANY GTK app from loading
  # incompatible system GIO modules (gvfs, dconf with GLIBC mismatch)
  home.sessionVariables.GIO_MODULE_DIR = gioModuleDir;

  systemd.user.services.swaync = {
    Unit = {
      Description = "Sway Notification Center";
      Documentation = "https://github.com/ErikReider/SwayNotificationCenter";
      After = [ "graphical-session.target" ];
      ConditionEnvironment = "WAYLAND_DISPLAY";
    };

    Service = {
      Type = "simple";
      ExecStart = "${swayncStart}";
      Restart = "always";
      RestartSec = "1s";
      # Also set GIO_MODULE_DIR in service environment for child processes
      Environment = [ "GIO_MODULE_DIR=${gioModuleDir}" ];
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };
}
