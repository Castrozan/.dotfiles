{ pkgs, ... }:
let
  pythonForQuitWindowlessApplicationsDaemon = pkgs.python312.withPackages (packages: [
    packages.pyobjc-core
    packages.pyobjc-framework-Cocoa
    packages.pyobjc-framework-Quartz
  ]);
in
{
  launchd.user.agents.quit-windowless-applications = {
    serviceConfig = {
      Label = "com.dotfiles.quit-windowless-applications";
      ProgramArguments = [
        "${pythonForQuitWindowlessApplicationsDaemon}/bin/python3"
        "${./quit-windowless-applications-daemon}"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/quit-windowless-applications.log";
      StandardErrorPath = "/tmp/quit-windowless-applications.log";
    };
  };
}
