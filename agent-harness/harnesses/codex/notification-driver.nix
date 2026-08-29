{
  isDarwin,
  linuxNotificationExecutablePath,
  linuxDesktopFocusExecutablePath,
}:
if isDarwin then
  {
    platform = "darwin";
    notificationExecutablePath = "/opt/homebrew/bin/alerter";
    desktopFocusExecutablePath = "/opt/homebrew/bin/hs";
  }
else
  {
    platform = "linux";
    notificationExecutablePath = linuxNotificationExecutablePath;
    desktopFocusExecutablePath = linuxDesktopFocusExecutablePath;
  }
