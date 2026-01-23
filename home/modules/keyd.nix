{ pkgs, ... }:
let
  # keyd-application-mapper is a Python script that needs to be available
  # We'll try to find it in the keyd package or use a wrapper
  keydAppMapper = pkgs.writeScriptBin "keyd-application-mapper" ''
    #!${pkgs.python3}/bin/python3
    import sys
    import os

    # Try to find keyd-application-mapper script
    keyd_share = "${pkgs.keyd}/share"
    script_paths = [
      "${pkgs.keyd}/bin/keyd-application-mapper",
      "${pkgs.keyd}/share/keyd/keyd-application-mapper",
      "${pkgs.keyd}/libexec/keyd-application-mapper",
    ]

    for path in script_paths:
        if os.path.exists(path):
            os.execv(path, sys.argv)

    # If not found, try to run it as a command (might be in PATH)
    os.execvp("keyd-application-mapper", sys.argv)
  '';

  # Application-specific leader key configuration
  # This file is used by keyd-application-mapper to apply per-application configs
  appConf = ''
    [ids]
    *

    # Obsidian: Super+O activates obsidian_layer
    [obsidian]
    meta.o = layer(obsidian_layer)

    # Brave: Super+B activates brave_layer
    [brave]
    meta.b = layer(brave_layer)
  '';
in
{
  # Create keyd application-specific configuration
  # Note: default.conf is now managed in nixos/modules/keyd.nix and written to /etc/keyd/default.conf
  home.file.".config/keyd/app.conf".text = appConf;

  # Configure keyd-application-mapper as a systemd user service
  systemd.user.services.keyd-application-mapper = {
    Unit = {
      Description = "keyd application mapper for per-application keybindings";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${keydAppMapper}/bin/keyd-application-mapper";
      Restart = "on-failure";
      RestartSec = "5s";
      # Prevent service from restarting too aggressively
      StartLimitIntervalSec = "60";
      StartLimitBurst = "3";
    };

    Install = {
      WantedBy = [ "default.target" ];
    };
  };

  # Enable the service to start automatically
  systemd.user.startServices = "sd-switch";
}
