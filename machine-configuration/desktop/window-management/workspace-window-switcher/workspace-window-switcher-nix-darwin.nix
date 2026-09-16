{
  lib,
  username,
  ...
}:
let
  swiftDaemonSourcesDirectory = ./swift-sources;
  swiftDaemonBinaryPath = "/usr/local/bin/workspace-window-switcher-daemon";
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    export SWIFT_BINARY_PATH=${lib.escapeShellArg swiftDaemonBinaryPath}
    export SWIFT_SOURCES_DIR=${swiftDaemonSourcesDirectory}
    export OWNER_USERNAME=${lib.escapeShellArg username}
    export SWIFT_COMPILE_RECIPE_HASH=${builtins.hashFile "sha256" ./compile.sh}
    ${builtins.readFile ./compile.sh}
  '';

  launchd.user.agents.workspace-window-switcher = {
    serviceConfig = {
      Label = "com.dotfiles.workspace-window-switcher";
      ProgramArguments = [ swiftDaemonBinaryPath ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/workspace-switcher.log";
      StandardErrorPath = "/tmp/workspace-switcher.log";
    };
  };
}
