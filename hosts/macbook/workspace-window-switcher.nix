{ pkgs, ... }:
let
  pythonForWindowSwitcherDaemon = pkgs.python312.withPackages (packages: [
    packages.pyobjc-core
    packages.pyobjc-framework-Cocoa
  ]);
in
{
  launchd.user.agents.workspace-window-switcher = {
    serviceConfig = {
      Label = "com.dotfiles.workspace-window-switcher";
      ProgramArguments = [
        "${pythonForWindowSwitcherDaemon}/bin/python3"
        "${./scripts/workspace-window-switcher-daemon}"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/workspace-switcher.log";
      StandardErrorPath = "/tmp/workspace-switcher.log";
    };
  };
}
