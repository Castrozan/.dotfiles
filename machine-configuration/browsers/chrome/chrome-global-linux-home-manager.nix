{
  pkgs,
  latest,
  hostname,
  ...
}:
let
  chromeForMachine = import ./chrome-linux-package.nix {
    inherit pkgs latest hostname;
  };

  chromeGlobalLauncher = pkgs.writeShellScript "chrome-global-launcher" ''
    exec ${chromeForMachine}/bin/google-chrome-stable \
      --user-data-dir="$HOME/.config/chrome-global" \
      --class=chrome-global \
      --enable-features=UseNativeNotifications,WebRTCPipeWireCapturer \
      "$@"
  '';

  desktopItem = pkgs.makeDesktopItem {
    name = "chrome-global";
    desktopName = "Chrome";
    genericName = "Web Browser";
    exec = "${chromeGlobalLauncher} %U";
    icon = "google-chrome";
    terminal = false;
    type = "Application";
    categories = [
      "Network"
      "WebBrowser"
    ];
    mimeTypes = [
      "text/html"
      "text/xml"
      "application/xhtml+xml"
      "application/xml"
      "x-scheme-handler/http"
      "x-scheme-handler/https"
    ];
  };
in
{
  home.packages = [
    chromeForMachine
    desktopItem
  ];

  xdg.dataFile."applications/chrome-global.desktop".source =
    "${desktopItem}/share/applications/chrome-global.desktop";
}
