{ pkgs, isDarwin }:
if isDarwin then
  {
    platform = "darwin";
    notificationExecutablePath = "/opt/homebrew/bin/alerter";
    desktopFocusExecutablePath = "/opt/homebrew/bin/hs";
  }
else
  {
    platform = "linux";
    notificationExecutablePath = "${pkgs.libnotify}/bin/notify-send";
    desktopFocusExecutablePath = "${pkgs.hyprland}/bin/hyprctl";
  }
