{ pkgs, ... }:
let
  forticlientLaunchScript = pkgs.writeShellScriptBin "forticlient-launch" (
    builtins.readFile ./scripts/forticlient-launch.sh
  );

  forticlientAuthCallbackScript = pkgs.writeShellScriptBin "forticlient-auth-callback" (
    builtins.readFile ./scripts/forticlient-auth-callback.sh
  );
in
{
  home.packages = [
    forticlientLaunchScript
    forticlientAuthCallbackScript
  ];

  xdg.desktopEntries.forticlient-launch = {
    name = "FortiClient";
    genericName = "VPN Client";
    exec = "forticlient-launch";
    icon = "forticlient";
    terminal = true;
    type = "Application";
    categories = [
      "Network"
      "Security"
    ];
  };

  xdg.desktopEntries.forticlient-auth-handler = {
    name = "FortiClient Auth Handler";
    exec = "forticlient-auth-callback %u";
    noDisplay = true;
    type = "Application";
    mimeType = [ "x-scheme-handler/fabricagent" ];
  };

  xdg.mimeApps.defaultApplications = {
    "x-scheme-handler/fabricagent" = "forticlient-auth-handler.desktop";
  };
}
