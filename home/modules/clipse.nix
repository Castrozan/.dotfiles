{ pkgs, ... }:
{
  # Add wl-clipboard as a dependency for clipse on Wayland
  home.packages = with pkgs; [
    wl-clipboard
  ];

  # Configure clipse as a systemd user service to run in the background
  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.clipse}/bin/clipse --listen";
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
