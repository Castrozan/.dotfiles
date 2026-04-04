{
  pkgs,
  lib,
  latest,
  ...
}:
let
  chromeGlobalUserDataDir = "$HOME/.config/chrome-global";

  chromeGlobalLauncher = pkgs.writeShellScript "chrome-global-launcher" ''
    exec ${latest.google-chrome}/bin/google-chrome-stable \
      --user-data-dir="${chromeGlobalUserDataDir}" \
      --class=chrome-global \
      --remote-debugging-port=0 \
      --enable-features=UseNativeNotifications,WebRTCPipeWireCapturer \
      "$@"
  '';

  enableChromeRemoteDebuggingInLocalState = pkgs.writeShellScript "enable-chrome-remote-debugging" ''
    set -euo pipefail
    LOCAL_STATE="${chromeGlobalUserDataDir}/Local State"
    if [ -f "$LOCAL_STATE" ]; then
      ${pkgs.jq}/bin/jq '.devtools.remote_debugging["user-enabled"] = true' "$LOCAL_STATE" | ${pkgs.moreutils}/bin/sponge "$LOCAL_STATE"
    fi
  '';
in
{
  home.packages = [ latest.google-chrome ];

  home.file.".config/chrome-global/policies/managed/chrome-remote-debugging.json".text =
    builtins.toJSON
      {
        RemoteDebuggingAllowed = true;
        DeveloperToolsAvailability = 0;
      };

  home.activation.enableChromeRemoteDebugging = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    run ${enableChromeRemoteDebuggingInLocalState}
  '';

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
