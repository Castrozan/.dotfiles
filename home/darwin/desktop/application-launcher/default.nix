{
  pkgs,
  config,
  lib,
  healthCheckLib,
  ...
}:
let
  applicationLauncherDaemonBinaryPath = "${config.home.homeDirectory}/.local/bin/application-launcher-daemon";
  applicationLauncherDaemonLaunchdLabel = "com.dotfiles.application-launcher-daemon";
  applicationLauncherDaemonSocketPath = "/tmp/application-launcher.sock";
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "application-launcher" ''
      exec ${pkgs.python312}/bin/python3 -c '
      import socket, sys
      client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
      try:
          client_socket.sendto(b"show", "${applicationLauncherDaemonSocketPath}")
      except OSError as exception:
          print(f"application-launcher: {exception}", file=sys.stderr)
          sys.exit(1)
      '
    '')
  ];

  home.activation.compileApplicationLauncherDaemon = config.lib.dag.entryAfter [ "writeBoundary" ] ''
    export SWIFT_BINARY_PATH=${lib.escapeShellArg applicationLauncherDaemonBinaryPath}
    export SWIFT_SOURCES_DIR=${./swift-sources}
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
