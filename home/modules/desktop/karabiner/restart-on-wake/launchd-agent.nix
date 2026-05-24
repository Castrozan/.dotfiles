{ pkgs, ... }:
let
  pythonInterpreterWithFrameworksForRestartOnWakeDaemon =
    pkgs.python312.withPackages
      (pythonPackages: [
        pythonPackages.pyobjc-core
        pythonPackages.pyobjc-framework-Cocoa
      ]);
in
{
  launchd.agents.karabiner-restart-on-wake = {
    enable = true;
    config = {
      Label = "com.dotfiles.karabiner-restart-on-wake";
      ProgramArguments = [
        "${pythonInterpreterWithFrameworksForRestartOnWakeDaemon}/bin/python3"
        "${./scripts/karabiner-restart-on-wake-daemon}"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/karabiner-restart-on-wake.log";
      StandardErrorPath = "/tmp/karabiner-restart-on-wake.log";
    };
  };
}
