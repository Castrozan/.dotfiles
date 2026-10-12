{
  pkgs,
  latest,
  hostname,
  ...
}:
let
  inherit
    (import ./broken-hardware-video-decoding/chrome-broken-hardware-video-decoding-workaround.nix {
      inherit pkgs;
      chromePackage = latest.google-chrome;
    })
    chromeWithoutBrokenHardwareVideoDecoding
    ;

  inherit
    (import ./nvidia-render-offload/chrome-nvidia-render-offload.nix {
      inherit pkgs hostname;
      chromePackage = chromeWithoutBrokenHardwareVideoDecoding;
      nvidiaRenderOffloadCommand = "/run/current-system/sw/bin/nvidia-offload";
    })
    chromeForMachine
    ;

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

  # Also place in ~/.local/share/applications/ (XDG_DATA_HOME) so xdg-open
  # finds it first. Without this, it only lives in ~/.nix-profile/share/
  # which is late in the search order and can be missed during rebuilds.
  xdg.dataFile."applications/chrome-global.desktop".source =
    "${desktopItem}/share/applications/chrome-global.desktop";
}
