{ pkgs, ... }:
let
  chromeGlobalLauncher = pkgs.writeShellScript "chrome-global-launcher" ''
    exec google-chrome-stable \
      --user-data-dir="$HOME/.config/chrome-global" \
      --class=chrome-global \
      --enable-features=UseNativeNotifications \
      "$@"
  '';
in
{

  xdg.desktopEntries.chrome-global = {
    name = "Chrome";
    genericName = "Web Browser";
    exec = "${chromeGlobalLauncher} %U";
    icon = "google-chrome";
    terminal = false;
    type = "Application";
    categories = [
      "Network"
      "WebBrowser"
    ];
    mimeType = [
      "text/html"
      "text/xml"
      "application/xhtml+xml"
      "application/xml"
      "x-scheme-handler/http"
      "x-scheme-handler/https"
    ];
  };

  xdg.mimeApps = {
    enable = true;
    defaultApplications = {
      "text/html" = "chrome-global.desktop";
      "text/xml" = "chrome-global.desktop";
      "application/xhtml+xml" = "chrome-global.desktop";
      "application/xml" = "chrome-global.desktop";
      "x-scheme-handler/http" = "chrome-global.desktop";
      "x-scheme-handler/https" = "chrome-global.desktop";
    };
  };
}
