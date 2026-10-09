{
  pkgs,
  config,
  lib,
  healthCheckLib,
  ...
}:
let
  applicationLauncherDaemonSourcesDirectory = pkgs.symlinkJoin {
    name = "application-launcher-daemon-swift-sources";
    paths = [
      ./swift-sources
      ../../input/command-sockets/swift-sources
    ];
  };
  applicationLauncherDaemonBinaryPath = "${config.home.homeDirectory}/.local/bin/application-launcher-daemon";
  applicationLauncherDaemonLaunchdLabel = "com.dotfiles.application-launcher-daemon";
  applicationLauncherDaemonSocketPath = "/tmp/application-launcher.sock";

  applicationLauncherClientSource = pkgs.writeText "application-launcher-client-source.py" (
    builtins.readFile ./scripts/application_launcher_client.py
  );
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "application-launcher" ''
      exec ${pkgs.python312}/bin/python3 ${applicationLauncherClientSource} ${lib.escapeShellArg applicationLauncherDaemonSocketPath}
    '')
  ];

  home.activation.compileApplicationLauncherDaemon = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    export SWIFT_BINARY_PATH=${lib.escapeShellArg applicationLauncherDaemonBinaryPath}
    export SWIFT_SOURCES_DIR=${applicationLauncherDaemonSourcesDirectory}
    export OWNER_USERNAME=${lib.escapeShellArg config.home.username}
    export LAUNCHD_LABEL=${lib.escapeShellArg applicationLauncherDaemonLaunchdLabel}
    export SWIFT_COMPILE_RECIPE_HASH=${builtins.hashFile "sha256" ./compile.sh}
    ${builtins.readFile ./compile.sh}
  '';

  launchd.agents.application-launcher-daemon = {
    enable = true;
    config = {
      Label = applicationLauncherDaemonLaunchdLabel;
      ProgramArguments = [ applicationLauncherDaemonBinaryPath ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/application-launcher-daemon.log";
      StandardErrorPath = "/tmp/application-launcher-daemon.log";
    };
  };

  healthCheck.probes = [
    (healthCheckLib.mkLaunchdProbe {
      name = "darwin app launcher daemon";
      label = applicationLauncherDaemonLaunchdLabel;
    })
  ];
}
